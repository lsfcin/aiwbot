# test_f6_voice_feedback.py — a voice note says something back before it has been transcribed
# (Lucas, 2026-07-28: "demora para aparecer qualquer feedback"). The download plus whisper take
# seconds, and silence for that long reads as being ignored.
import asyncio
from frontend import bot, turnrun
from .test_route_text import FakeMsg, FakeReplyAnchor


def test_a_voice_note_is_acknowledged_before_the_transcription_runs(store, monkeypatch):
    """Whisper takes seconds and the download takes more, so an audio turn used to sit silent
    long enough to read as "the bot ignored me". The status goes out FIRST, and it names what is
    happening rather than saying ok."""
    order = []

    class _Msg:
        reply_to_message = None
        forward_origin = None

        async def reply_text(self, text, parse_mode=None, do_quote=False, reply_markup=None):
            order.append(("said", text))
            return FakeReplyAnchor(7)

    async def fake_save(file_id, context, suffix):
        order.append(("downloaded", None))
        return "/tmp/x.ogg"

    monkeypatch.setattr(bot.inbox, "save_media", fake_save)
    monkeypatch.setattr(bot.stt, "transcribe", lambda p: order.append(("transcribed", None)) or "bot faz isso")

    async def fake_route(msg, text, context, *, spoken=False, working=None):
        order.append(("routed", working))

    monkeypatch.setattr(bot, "_route_text", fake_route)
    msg = _Msg()
    msg.voice = type("V", (), {"file_id": "f"})()
    asyncio.run(bot._handle_voice(msg, None))

    steps = [step for step, _ in order]
    assert steps == ["said", "downloaded", "transcribed", "routed"]
    assert order[-1][1] is not None, "the status bubble must be handed to the turn, not abandoned"


def test_the_status_bubble_becomes_the_turns_working_message(store, monkeypatch):
    """One bubble, morphed — not a status followed by a second "trabalhando…" message."""
    edited = []

    async def fake_edit(message, text, markup=None):
        edited.append(text)
        return True

    monkeypatch.setattr(turnrun.reply, "edit_text", fake_edit)

    async def fake_safe_reply(msg, text, reply_markup=None):
        raise AssertionError("a second status bubble was sent")

    monkeypatch.setattr(turnrun.reply, "safe_reply", fake_safe_reply)
    existing = FakeReplyAnchor(7)
    result = asyncio.run(turnrun._working(FakeMsg(), existing))
    assert result is existing
    assert edited, "the status was left saying it was still transcribing"
