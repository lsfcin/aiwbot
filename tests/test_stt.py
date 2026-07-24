# test_stt.py — free unit test: STT wrapper (C1 transcription, C3 fail-safe, C6 no live calls).
import pathlib
from frontend import stt


class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeModel:
    """Stands in for faster_whisper.WhisperModel: transcribe(path, language, hotwords) ->
    (segments, info). No real model load, no audio decode — a fixture, not a live call."""

    def __init__(self, segments):
        self._segments = segments
        self.calls = []

    def transcribe(self, path, language="pt", hotwords=None, **kw):
        self.calls.append((path, language, hotwords))
        return iter(self._segments), None


def test_run_joins_segment_texts_and_passes_hotwords_through():
    model = FakeModel([FakeSegment(" oi"), FakeSegment(" tudo bem")])
    text = stt.run(pathlib.Path("/tmp/x.ogg"), model, hotwords="opencode, aiwbot")
    assert text.strip() == "oi tudo bem"
    assert model.calls[0][2] == "opencode, aiwbot"


def test_transcribe_lazily_loads_model_and_hotwords_prompt(monkeypatch):
    model = FakeModel([FakeSegment("oi bot")])
    monkeypatch.setattr(stt, "_model", lambda: model)
    monkeypatch.setattr("frontend.hotwords.as_prompt", lambda: "opencode, aiwbot")
    result = stt.transcribe(pathlib.Path("/tmp/x.ogg"))
    assert result.strip() == "oi bot"


def test_transcribe_returns_empty_string_on_exception(monkeypatch):
    class BoomModel:
        def transcribe(self, *a, **kw):
            raise RuntimeError("decode failed")

    monkeypatch.setattr(stt, "_model", lambda: BoomModel())
    result = stt.transcribe(pathlib.Path("/tmp/bad.ogg"))
    assert result == ""
