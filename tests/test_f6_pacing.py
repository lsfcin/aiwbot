# test_f6_pacing.py — the pause BETWEEN bubbles (Lucas, 2026-07-28). Distinct from the repaint
# floor in test_f4_streaming.py, and that distinction is the whole point: MIN_INTERVAL paces edits
# to the live bubble, BUBBLE_GAP paces the conversation. Confusing the two is why the cadence
# looked like it did nothing — "o tempo entre bubbles não funcionou".
import asyncio
from frontend import cadence, painter
from .chatkit import Bubble, Origin
from .streamkit import Clock


def _paced(gap: float, deltas: int = 24):
    """Feed a long answer at `gap` seconds per delta; report when each bubble was BORN.

    Birth is when the bubble is sent, not when it is anchored: bubble one is the working message
    the painter starts from, and it is anchored later, retroactively, the moment the session id
    arrives (AD-23). Measuring anchors would read that as a bubble appearing mid-turn."""
    origin = Origin()
    clock = Clock()
    born = [clock.now]
    sending = origin.reply_text

    async def timed(text, **kw):
        born.append(clock.now)
        return await sending(text, **kw)

    origin.reply_text = timed
    live = painter.Painter(Bubble(origin.chat), "pensando…", clock=clock, origin=origin,
                           on_bubble=lambda b, sid: None)

    async def run():
        for i in range(deltas):
            clock.advance(gap)
            await live.paint(f"paragrafo {i} " + "palavra " * 60 + "\n\n", session_id="s1")

    asyncio.run(run())
    return live, born


def test_bubbles_are_paced_apart_even_when_the_stream_outruns_them():
    live, born = _paced(gap=1.0)
    assert len(born) > 2, "the corpus did not produce enough bubbles"
    gaps = [b - a for a, b in zip(born, born[1:])]
    assert min(gaps) >= cadence.BUBBLE_GAP


def test_only_one_bubble_is_born_per_paint():
    """However far the stream has run ahead, a paint posts at most one bubble: posting every
    chunk that already fits would land three in the same second and undo the pause."""
    live, born = _paced(gap=1.0)
    assert len(set(born)) == len(born), "two bubbles were born at the same instant"


def test_text_held_back_by_the_pause_is_not_lost():
    """The pause delays a bubble, it never drops what the bubble was going to say."""
    fast, _ = _paced(gap=1.0)
    slow, _ = _paced(gap=10.0)
    assert fast.text == slow.text
    shown = "".join(b.text for b in fast.sent)
    assert "paragrafo 0" in shown


def test_the_first_bubble_is_never_held_back():
    """The pause belongs between bubbles, not in front of the answer: the working message becomes
    bubble one immediately, so a turn never opens on a silent gap."""
    live, born = _paced(gap=0.5, deltas=6)
    assert live.sent, "the answer never reached the chat"


def test_a_slow_stream_is_not_slowed_further():
    """A stream that already arrives slower than the gap must pass through untouched — the pause
    is a floor, never a delay added on top."""
    fast, fast_born = _paced(gap=1.0)
    slow, slow_born = _paced(gap=10.0)
    assert len(slow_born) >= len(fast_born)
