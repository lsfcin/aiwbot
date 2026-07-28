# test_f6_bubble_shape.py — the furniture on a bubble, decided by Lucas on 2026-07-28: the voice
# transcript quoted INSIDE every bubble instead of in one of its own, a position marker at the end
# of each, and `·` never opening a line. What a bubble is made of, not how it is split.
import asyncio
from frontend import answer, painter, phrases, reply
from .chatkit import Bubble, Origin
from .streamkit import Clock


def _chunks(n: int, size: int = 500) -> list[str]:
    return [f"paragrafo {i} " + "x" * size for i in range(n)]


def test_the_transcript_opens_every_bubble_not_a_bubble_of_its_own():
    """Lucas: "cada bubble ter a transcrição quoted em itálico no início". A separate echo bubble
    scrolls out of reach the moment the answer is longer than a screen."""
    lead = answer.quote("me explica o ciclo da água")
    decorated = answer.decorate(_chunks(3), lead)
    for bubble in decorated:
        assert bubble.startswith(lead)
        assert "<blockquote>" in bubble and "<i>" in bubble


def test_the_quoted_transcript_is_escaped_and_clipped():
    """It is Lucas's own words, so it can contain anything, including HTML and a two-minute
    monologue — neither may reach Telegram as-is."""
    lead = answer.quote("<b>oi</b> & tchau " + "palavra " * 200)
    assert "&lt;b&gt;" in lead and "&amp;" in lead
    assert len(lead) < answer.LEAD_CHARS + 60


def test_a_single_bubble_answer_is_not_numbered():
    only = answer.decorate(["texto"], total=1)
    assert only == ["texto"]


def test_every_bubble_says_where_it_sits():
    numbered = answer.decorate(_chunks(3), total=3)
    assert numbered[0].endswith("(1/3)")
    assert numbered[2].endswith("(3/3)")


def test_a_bubble_born_mid_stream_counts_without_a_total():
    """The total is unknowable while the answer is still arriving — bubble 3 exists only once the
    text that fills it does. A sealed bubble is never rewritten (AD-25), so it shows the count it
    could know, and the finished answer is where `(n/N)` appears."""
    live = answer.decorate(_chunks(2))
    assert live[0].endswith("(1)")
    assert "/" not in live[0][-6:]


def test_the_furniture_is_paid_for_before_the_split_not_after():
    """Reserved up front: a chunk sized to the full limit and THEN given a lead and a counter is
    a message Telegram rejects — and it would only ever happen on a long voice answer."""
    lead = answer.quote("uma pergunta razoavelmente longa sobre o ciclo da água")
    body = "\n\n".join(f"paragrafo {i} " + "palavra " * 120 for i in range(12))
    frames = answer.frames(body, limit=reply.TELEGRAM_MSG_LIMIT, soft=reply.SOFT_CHARS, lead=lead)
    assert len(frames) > 1
    for frame in frames:
        assert len(frame) <= reply.TELEGRAM_MSG_LIMIT


def test_a_streamed_voice_answer_keeps_the_quote_on_every_bubble():
    """End to end through the painter: the lead survives sealing, so a bubble Lucas scrolls back
    to still says which question it answers."""
    lead = answer.quote("me explica o ciclo da água")
    origin = Origin()
    clock = Clock()
    live = painter.Painter(Bubble(origin.chat), "pensando…", clock=clock, origin=origin, lead=lead)

    async def go():
        for i in range(12):
            clock.advance(10)
            await live.paint(f"paragrafo {i} " + "palavra " * 60 + "\n\n", session_id="s1")

    asyncio.run(go())
    assert len(live.sent) > 1, "the corpus did not produce a second bubble"
    for bubble in live.sent:
        assert "<blockquote>" in bubble.text
        assert len(bubble.text) <= reply.TELEGRAM_MSG_LIMIT


def test_the_pin_sits_below_the_counter():
    """Order on the live bubble: answer, then where it sits, then the status hanging under it."""
    frames = answer.frames("texto " * 400, pin="pensando…", limit=1000, soft=400)
    assert frames[-1].endswith("pensando…")
    assert frames[0].rstrip().endswith("(1)")


def test_the_status_line_never_opens_with_the_divider():
    assert not phrases.pin().startswith("·")
