# test_route_text.py — free unit test: shared text/voice routing (_route_text), the C3
# empty-transcript guard, and the C5 spoken-flag threading into run_and_deliver.
import asyncio
from frontend import bot, msgmap, phrases, registry, turnrun


class FakeReplyAnchor:
    def __init__(self, message_id):
        self.message_id = message_id


class FakeMsg:
    def __init__(self, reply_to_message_id=None):
        self.reply_to_message = FakeReplyAnchor(reply_to_message_id) if reply_to_message_id else None


def test_route_text_bot_prefix_starts_new_session_with_spoken_flag(store, monkeypatch):
    calls = []

    async def fake_start_new(msg, prompt, *, spoken=False):
        calls.append((prompt, spoken))

    monkeypatch.setattr(turnrun, "start_new", fake_start_new)
    asyncio.run(bot._route_text(FakeMsg(), "bot faz isso", None, spoken=True))
    assert calls == [("faz isso", True)]


def test_route_text_reply_continue_threads_spoken_flag(store, monkeypatch):
    msgmap.remember_reply(42, "s1")
    calls = []

    async def fake_reply_continue(msg, sid, text, *, spoken=False):
        calls.append((sid, text, spoken))

    monkeypatch.setattr(turnrun, "handle_reply_continue", fake_reply_continue)
    msg = FakeMsg(reply_to_message_id=42)
    asyncio.run(bot._route_text(msg, "oi, continua", None, spoken=True))
    assert calls == [("s1", "oi, continua", True)]


def test_route_text_reply_continue_forwards_transcript_not_msg_text(store, monkeypatch):
    """Regression for the flagged 4b-code.md gap: a voice message replying to a prior session
    anchor has msg.text=None (only the STT transcript carries the content). _route_text must
    forward the resolved `text` argument into _handle_reply_continue, not let it re-derive the
    prompt from msg.text — otherwise a voice-note reply-continue would dispatch on None/stale
    content, violating the C3 "never dispatch on wrong content" spirit."""
    msgmap.remember_reply(42, "s1")
    calls = []

    async def fake_reply_continue(msg, sid, text, *, spoken=False):
        calls.append(text)

    monkeypatch.setattr(turnrun, "handle_reply_continue", fake_reply_continue)
    msg = FakeMsg(reply_to_message_id=42)
    msg.text = None  # a real voice Update's Message.text is None; only the transcript has content
    asyncio.run(bot._route_text(msg, "faz o deploy", None, spoken=True))
    assert calls == ["faz o deploy"]


def test_handle_reply_continue_dispatches_with_passed_text_not_msg_text(store, monkeypatch):
    """Direct-level companion to the regression above: even called on its own, _handle_reply_
    continue must run the turn on its `text` argument, never on `msg.text` — the real defect
    this guards is `run_and_deliver(msg, working, msg.text, ...)` silently reading None (or
    stale content) for a voice message that has no `.text` at all."""
    prompts = []

    async def fake_safe_reply(msg, html, reply_markup=None):
        return None

    async def fake_run_and_deliver(msg, working, prompt, *, session_id, backend_name, title, scope, spoken=False):
        prompts.append(prompt)

    monkeypatch.setattr(turnrun.reply, "safe_reply", fake_safe_reply)
    monkeypatch.setattr(turnrun, "run_and_deliver", fake_run_and_deliver)
    msg = FakeMsg()
    msg.text = None  # real voice Update.message.text
    asyncio.run(turnrun.handle_reply_continue(msg, "s1", "transcrito da fala", spoken=True))
    assert prompts == ["transcrito da fala"]


def test_empty_guard_true_for_blank_or_whitespace_transcript():
    assert bot._empty_guard("") is True
    assert bot._empty_guard("   ") is True


def test_empty_guard_false_for_real_transcript():
    assert bot._empty_guard("oi bot, faz isso") is False


def test_transcribe_fail_phrases_is_a_nonempty_pt_bank():
    assert isinstance(phrases.TRANSCRIBE_FAIL_PHRASES, list)
    assert len(phrases.TRANSCRIBE_FAIL_PHRASES) > 0
    assert all(isinstance(p, str) and p for p in phrases.TRANSCRIBE_FAIL_PHRASES)


def testrun_and_deliver_spoken_sends_voice_in_addition_to_text(store, monkeypatch):
    sent = {"voice": None, "text": None}

    class FakeResult:
        text = "resposta"
        session_id = "s1"
        cost_usd = 0.0
        model = None
        context_used = None
        context_window = None

    async def fake_turn(*a, **kw):
        return FakeResult()

    async def fake_deliver(working, msg, block, reply_markup=None, lead=""):
        sent["text"] = block
        sent["lead"] = lead
        # deliver returns EVERY bubble it sent (F5a), so the caller can anchor them all.
        return []

    async def fake_send_voice(msg, ogg_bytes):
        sent["voice"] = ogg_bytes
        return None

    monkeypatch.setattr(turnrun.dispatch, "turn", fake_turn)
    monkeypatch.setattr(turnrun.reply, "deliver", fake_deliver)
    monkeypatch.setattr(turnrun.reply, "send_voice", fake_send_voice)
    monkeypatch.setattr(turnrun, "tts", type("FakeTTS", (), {"synthesize": staticmethod(lambda t: b"OGG")}))
    asyncio.run(turnrun.run_and_deliver(FakeMsg(), None, "prompt", session_id=None,
                                      backend_name="claude", title=None, scope=registry.NEW,
                                      spoken=True))
    assert sent["voice"] == b"OGG"
    # The transcript rides inside the answer now, quoted, instead of in a bubble of its own.
    assert "prompt" in sent["lead"] and "<blockquote>" in sent["lead"]


def testrun_and_deliver_not_spoken_never_sends_voice(store, monkeypatch):
    sent = {"voice_called": False}

    class FakeResult:
        text = "resposta"
        session_id = "s1"
        cost_usd = 0.0
        model = None
        context_used = None
        context_window = None

    async def fake_turn(*a, **kw):
        return FakeResult()

    async def fake_deliver(working, msg, block, reply_markup=None, lead=""):
        sent["lead"] = lead
        return []

    async def fake_send_voice(msg, ogg_bytes):
        sent["voice_called"] = True
        return None

    monkeypatch.setattr(turnrun.dispatch, "turn", fake_turn)
    monkeypatch.setattr(turnrun.reply, "deliver", fake_deliver)
    monkeypatch.setattr(turnrun.reply, "send_voice", fake_send_voice)
    asyncio.run(turnrun.run_and_deliver(FakeMsg(), None, "prompt", session_id=None,
                                      backend_name="claude", title=None, scope=registry.NEW,
                                      spoken=False))
    assert sent["voice_called"] is False
    assert sent["lead"] == "", "a typed turn has nothing to echo"


def test_bot_no_longer_owns_running_a_turn():
    """Stage 0 of F4: `bot.py` is PTB wiring + routing, `turnrun.py` runs a turn and puts its
    answer on screen. F4 changes only the latter, so the two must not re-fuse — if `bot` starts
    importing `dispatch` again, the seam the streaming work needs has been lost."""
    assert not hasattr(bot, "dispatch")
    assert not hasattr(bot, "answer")
    assert hasattr(turnrun, "dispatch")
