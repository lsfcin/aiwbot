# painter.py — keep the chat showing the answer as it arrives, throttled. One object per turn.
from __future__ import annotations
import time
from . import answer, markdown, reply
from .cadence import Cadence
from .htmlsplit import split_html

# Stage 3's rollback: off, a streamed answer stays in one bubble that freezes when it outgrows a
# message, exactly as Stage 2 shipped. Independent of the `stream` knob on purpose, so sealing
# can be reverted without giving up live text.
STREAM_SEAL = True


class Painter:
    """Owns the accumulating answer and the bubbles it is being written into.

    Per turn, never global: it dies with the turn, so nothing has to be reset or cleaned up.
    The buffer lives here rather than in `dispatch` because `on_text` receives DELTAS — the
    authoritative join still happens in `events_to_result` at the end, so even a painter that
    drifted could not corrupt the delivered answer."""

    def __init__(self, working, pin: str, clock=time.monotonic, origin=None,
                 on_bubble=None, seal: bool = STREAM_SEAL, lead: str = ""):
        self.pin = pin
        # The quoted transcript that opens every bubble of a voice turn; "" for a typed one.
        self.lead = lead
        self.clock = Cadence(clock)
        self.origin = origin
        self.on_bubble = on_bubble
        self.seal = seal and origin is not None
        self.sent = [working] if working is not None else []
        self.pending = list(self.sent)
        self.session_id: str | None = None
        self.text = ""
        self.busy = False
        self.frozen = False

    # --- anchoring ---------------------------------------------------------------------------

    async def note_session(self, session_id: str | None) -> None:
        """AD-23: a bubble is repliable only once it is mapped to its session. The id usually
        arrives before any text (claude's `system:init`), but nothing here DEPENDS on that —
        bubbles born earlier queue up and are anchored retroactively the moment it is known."""
        if not session_id or self.session_id:
            return
        self.session_id = session_id
        # Drained into a snapshot and emptied BEFORE anchoring, never iterated in place: an
        # `_anchor` that re-queued while this loop walked the same list would append forever and
        # eat the machine's memory. Structural, so the loop is impossible rather than merely
        # unlikely (found 2026-07-28 by a Painter built without `on_bubble`).
        queued = self.pending
        self.pending = []
        for bubble in queued:
            self._anchor(bubble)

    def _anchor(self, bubble) -> None:
        """Queue only for the reason queuing exists — the session id is not known yet. A painter
        with no `on_bubble` has nowhere to anchor TO, which is a different condition and must not
        re-queue: conflating the two is what made the drain above unbounded."""
        if not self.session_id:
            self.pending.append(bubble)
        elif self.on_bubble is not None:
            self.on_bubble(bubble, self.session_id)

    # --- throttle ----------------------------------------------------------------------------

    def _due(self) -> bool:
        """Is a repaint worth a round trip right now? Timing is `cadence`'s call; what this adds
        is the painter's own state.

        `busy` DROPS a paint rather than queueing it, which is lossless: every frame is recomputed
        from the whole accumulated text, so a skipped one is simply superseded by the next. That
        is what stops a fast stream from piling up requests behind a slow round trip."""
        result = False
        if self.sent and not self.frozen and not self.busy:
            result = self.clock.due(len(self.text))
        return result

    async def _keep_typing(self) -> None:
        """Re-light Telegram's own "typing…" indicator while the gate above says nothing else
        should move."""
        lit = self.clock.typing_due()
        if lit:
            await reply.send_typing(self.sent[0])

    # --- painting ----------------------------------------------------------------------------

    def frames(self) -> list[str]:
        """The bubbles this answer occupies right now: settled markdown rendered, the still
        arriving tail as plain text, pin on the last one."""
        settled, unsettled = markdown.stable_prefix(self.text)
        soft = reply.SOFT_CHARS if self.seal else None
        chunks = answer.frames(settled, unsettled, pin=self.pin,
                               limit=reply.TELEGRAM_MSG_LIMIT, soft=soft, lead=self.lead)
        if not self.seal and len(chunks) > 1:
            # Stage 2 behaviour: one bubble that stops updating once the answer outgrows a
            # message, leaving the finished delivery to do the splitting.
            self.frozen = True
        return chunks

    async def _grow(self, chunks: list[str]) -> None:
        """New bubbles were born since the last paint.

        Safe only because `split_html` is prefix-stable: every chunk but the last is final, so a
        bubble can be sent the moment it appears and never touched again. It is anchored on
        arrival, which makes AD-23 continuous — Lucas can reply to bubble 1 while bubble 3 is
        still being written."""
        closing = len(self.sent) - 1
        await reply.edit_text(self.sent[closing], chunks[closing])
        # Exactly ONE bubble per paint, however far the stream has run ahead. Posting every chunk
        # that fits would land three bubbles in the same second and undo the pause entirely — the
        # rest wait for their own gap, and `finish` ships whatever is still owed at the end.
        chunk = chunks[len(self.sent)]
        bubble = await reply.safe_reply(self.origin, chunk)
        if bubble is not None:
            self.sent.append(bubble)
            self._anchor(bubble)
            self.clock.mark_bubble()

    async def finish(self, block: str, markup=None) -> list:
        """Land the finished answer on the bubbles already on screen.

        Only the live bubble and anything after it is written: prefix-stability means the sealed
        ones already hold exactly their final text, so re-sending them would duplicate the answer
        and re-editing them would spend round trips to change nothing. The footer and keyboard
        only ever affect the last chunk, and the pin disappears because `block` has none."""
        budget = answer.room(reply.TELEGRAM_MSG_LIMIT, self.lead)
        chunks = split_html(block, budget, reply.SOFT_CHARS)
        chunks = answer.decorate(chunks, self.lead, total=len(chunks))
        live = len(self.sent) - 1
        for i in range(live, len(chunks)):
            last = i == len(chunks) - 1
            tail_markup = markup if last else None
            if i < len(self.sent):
                await reply.edit_text(self.sent[i], chunks[i], tail_markup)
            else:
                bubble = await reply.safe_reply(self.origin, chunks[i], reply_markup=tail_markup)
                if bubble is None:
                    break
                self.sent.append(bubble)
                self._anchor(bubble)
        await self._stamp(chunks, live)
        return list(self.sent)

    async def _stamp(self, chunks: list[str], live: int) -> None:
        """One closing pass over the bubbles already sealed, so each ends `(2/3)` instead of the
        `(2)` it was born with. Lucas asked for exact positions everywhere (2026-07-28).

        This is the ONE moment a sealed bubble is rewritten, and it is why the rule is "sealed
        bubbles are not rewritten *while the answer is streaming*" rather than "never": the total
        cannot exist before the end, and prefix-stability guarantees the only difference is the
        counter — nothing Lucas has read changes under him. It runs AFTER the live bubble is
        finished, so the answer completes first and the stamping trails it."""
        for i in range(min(live, len(chunks))):
            await reply.edit_text(self.sent[i], chunks[i])

    async def paint(self, delta: str, session_id: str | None = None) -> None:
        self.text += delta
        await self.note_session(session_id)
        if not self.sent:
            return
        await self._keep_typing()
        if not self._due():
            return
        chunks = self.frames()
        growing = self.seal and len(chunks) > len(self.sent)
        if growing and not self.clock.spaced():
            # The live bubble is already past its soft size, so there is nothing worth showing in
            # it meanwhile: the held text lands whole as the next bubble once the gap has passed.
            return
        self.busy = True
        if growing:
            await self._grow(chunks)
            ok = True
        else:
            ok = await reply.edit_text(self.sent[-1], chunks[len(self.sent) - 1])
        self.busy = False
        self.clock.mark_paint(len(self.text), ok)
