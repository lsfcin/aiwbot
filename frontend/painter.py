# painter.py — keep the chat showing the answer as it arrives, throttled. One object per turn.
from __future__ import annotations
import time
from . import answer, markdown, reply
from .htmlsplit import split_html

# Telegram tolerates roughly one edit per second per message, so this is a UX number rather than
# a rate-limit one: the answer should arrive like someone typing, not like a progress bar. Set to
# 5 s and then to 3 s by Lucas on 2026-07-27, reading real turns in the chat — tune it there, not
# from theory. The chunky bursts claude actually streams in suit a slower cadence anyway.
MIN_INTERVAL = 3.0
# Telegram's typing indicator lasts about five seconds, so it has to be re-sent to stay lit. Sent
# slightly ahead of that, it reads as continuous. This is the signal that carries the gap BETWEEN
# repaints — without it a 3 s pause looks like the bot died (Lucas's ask, 2026-07-27).
TYPING_EVERY = 4.0
# Below this a repaint spends a ~200 ms round trip (AD-20) to move almost nothing.
MIN_GROWTH = 40
# A failed paint widens the gap rather than retrying, so a rate-limited stream backs off instead
# of piling on. Success decays it back toward the floor.
MAX_INTERVAL = 10.0
_BACKOFF = 2.0
_DECAY = 0.5
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
        self.clock = clock
        self.origin = origin
        self.on_bubble = on_bubble
        self.seal = seal and origin is not None
        self.sent = [working] if working is not None else []
        self.pending = list(self.sent)
        self.session_id: str | None = None
        self.text = ""
        self.painted = 0
        self.last_at = 0.0
        self.typing_at = 0.0
        self.interval = MIN_INTERVAL
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
        """Is a repaint worth a round trip right now?

        `busy` DROPS a paint rather than queueing it, which is lossless: every frame is recomputed
        from the whole accumulated text, so a skipped one is simply superseded by the next. That
        is what stops a fast stream from piling up requests behind a slow round trip."""
        if not self.sent or self.frozen or self.busy:
            return False
        if len(self.text) - self.painted < MIN_GROWTH:
            return False
        return self.clock() - self.last_at >= self.interval

    def _retune(self, ok: bool) -> None:
        if ok:
            self.interval = max(MIN_INTERVAL, self.interval * _DECAY)
        else:
            self.interval = min(MAX_INTERVAL, self.interval * _BACKOFF)

    async def _keep_typing(self) -> None:
        """Re-light Telegram's own "typing…" indicator. Independent of the repaint gate on
        purpose: it starts on the FIRST delta, long before enough text has accumulated to be
        worth a repaint, so the gap before the first visible words is never silent."""
        now = self.clock()
        if now - self.typing_at < TYPING_EVERY:
            return
        self.typing_at = now
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
        for chunk in chunks[len(self.sent):]:
            bubble = await reply.safe_reply(self.origin, chunk)
            if bubble is None:
                break
            self.sent.append(bubble)
            self._anchor(bubble)

    async def finish(self, block: str, markup=None) -> list:
        """Land the finished answer on the bubbles already on screen.

        Only the live bubble and anything after it is written: prefix-stability means the sealed
        ones already hold exactly their final text, so re-sending them would duplicate the answer
        and re-editing them would spend round trips to change nothing. The footer and keyboard
        only ever affect the last chunk, and the pin disappears because `block` has none."""
        budget = answer.room(reply.TELEGRAM_MSG_LIMIT, self.lead)
        chunks = split_html(block, budget, reply.SOFT_CHARS)
        # The total is knowable only here, at the end, so this is the one place `(n/N)` can be
        # written. Sealed bubbles keep the `(n)` they were born with rather than being rewritten.
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
        return list(self.sent)

    async def paint(self, delta: str, session_id: str | None = None) -> None:
        self.text += delta
        await self.note_session(session_id)
        if not self.sent:
            return
        await self._keep_typing()
        if not self._due():
            return
        self.busy = True
        chunks = self.frames()
        if self.seal and len(chunks) > len(self.sent):
            await self._grow(chunks)
            ok = True
        else:
            ok = await reply.edit_text(self.sent[-1], chunks[len(self.sent) - 1])
        self.busy = False
        self.last_at = self.clock()
        self.painted = len(self.text)
        self._retune(ok)
