# stt.py — STT wrapper: faster-whisper large-v3-turbo, lazy-loaded; fails safe to "" (C1, C3).
from __future__ import annotations
import pathlib
from . import hotwords as hotwords_data

_MODEL_NAME = "large-v3-turbo"
_cached_model = None


def _model():
    """Lazy-cached WhisperModel. faster_whisper is imported *inside* here, never at module
    top, so make test can import this module without the (heavy, optional) dep installed."""
    global _cached_model
    if _cached_model is None:
        from faster_whisper import WhisperModel
        _cached_model = WhisperModel(_MODEL_NAME, device="cpu", compute_type="int8")
    return _cached_model


def run(path: pathlib.Path, model, hotwords: str) -> str:
    """Transcribe one file with an injectable model — the C1/C3 test seam. Any failure
    (bad audio, model error) degrades to "" rather than raising: the C3 fail-safe invariant."""
    text = ""
    try:
        segments, _info = model.transcribe(str(path), language="pt", hotwords=hotwords)
        text = "".join(seg.text for seg in segments)
    except Exception as e:
        print(f"stt.run failed: {e}")
        text = ""
    return text.strip()


def transcribe(path: pathlib.Path) -> str:
    return run(path, _model(), hotwords_data.as_prompt())
