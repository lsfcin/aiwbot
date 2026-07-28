# painter.py — keep the chat showing the answer as it arrives, throttled. One object per turn.
from __future__ import annotations
import time
from . import answer, markdown, reply

# Telegram tolerates roughly one edit per second per message. 1.5 s leaves headroom and, at
# typical token rates, adds ~100 visible characters per tick — alive to read, without flicker.
MIN_INTERVAL = 1.5
# Below this a repaint spends a ~200 ms round trip (AD-20) to move almost nothing.
MIN_GROWTH = 40
# A failed paint widens the gap rather than retrying, so a rate-limited stream backs off instead
# of piling on. Success decays it back toward the floor.
MAX_INTERVAL = 10.0
_BACKOFF = 2.0
_DECAY = 0.5


class Painter:
    """Owns the accumulating answer and the live bubble it is being written into.

    Per turn, never global: it dies with the turn, so nothing has to be reset or cleaned up.
    The buffer lives here rather than in `dispatch` because `on_text` receives DELTAS — the
    authoritative join still happens in `events_to_result` at the end, so even a painter that
    drifted could not corrupt the delivered answer."""

    def __init__(self, working, pin: str, clock=time.monotonic):
        self.working = working
        self.pin = pin
        self.clock = clock
        self.text = ""
        self.painted = 0
        self.last_at = 0.0
        self.interval = MIN_INTERVAL
        self.busy = False
        self.frozen = False
        self.paints = 0

    def _due(self) -> bool:
        """Is a repaint worth a round trip right now?

        `busy` DROPS a paint rather than queueing it, which is lossless: every frame is recomputed
        from the whole accumulated text, so a skipped one is simply superseded by the next. That
        is what stops a fast stream from piling up requests behind a slow round trip."""
        if self.working is None or self.frozen or self.busy:
            return False
        if len(self.text) - self.painted < MIN_GROWTH:
            return False
        return self.clock() - self.last_at >= self.interval

    def frame(self) -> str:
        """What the live bubble should show: settled markdown rendered, the still-arriving tail
        as plain text, and the pin last so it reads as "still going"."""
        settled, unsettled = markdown.stable_prefix(self.text)
        chunks = answer.frames(settled, unsettled, pin=self.pin)
        # Stage 2 paints a single bubble. Once the answer outgrows one Telegram message the
        # preview freezes and the finished delivery does the splitting, exactly as it does today
        # — Stage 3 is what turns that into bubbles sealed as they are born.
        if len(chunks) > 1:
            self.frozen = True
        return chunks[0]

    async def paint(self, delta: str) -> None:
        self.text += delta
        if not self._due():
            return
        self.busy = True
        body = self.frame()
        ok = await reply.edit_text(self.working, body)
        self.busy = False
        self.last_at = self.clock()
        self.painted = len(self.text)
        self.paints += 1
        self._retune(ok)

    def _retune(self, ok: bool) -> None:
        if ok:
            widened = self.interval * _DECAY
            self.interval = max(MIN_INTERVAL, widened)
        else:
            widened = self.interval * _BACKOFF
            self.interval = min(MAX_INTERVAL, widened)
