# SPEC: frontend — audio-in-out voice pipeline
<!-- Machine-parseable module contract (spec-driven development). Keep the header keys below. -->
spec-version: 0
status: locked
verify: none

<!-- Scope: the voice surface added by feature/audio-in-out (STT in, TTS out) over the existing
     Telegram frontend. Non-voice files (bot text routing, dispatch, format, inbox, reply text
     paths) keep their prior behavior; this contract governs the new/changed voice boundaries.
     Loop 6 folds the Carry criteria + Loop-3 seams here and flips status -> locked. -->

## Inputs
- A Telegram voice note: `voice.file_id: str` reaching `bot._handle_message`.
- `hotwords.HOTWORDS: list[str]` — explicit editable literal (workspace jargon + EN loanwords), no inline strings (C4).
- On voice-out: the delivered turn text `result.text: str` (plain-stripped via `format.plain`, clipped to a sane cap).
- `stt.run` accepts an injectable `model` (the C1/C3 test seam); `tts.encode_ogg` accepts a synthetic numpy waveform + `sample_rate: int` (the C5 test seam).

## Outputs
- `hotwords.as_prompt() -> str` — HOTWORDS joined by spaces for faster-whisper's `hotwords=` arg.
- `stt.run(path: Path, model) -> str` and `stt.transcribe(path: Path) -> str` — transcript text; `""` on empty/exception (C1/C3).
- `tts.encode_ogg(samples, sample_rate: int) -> bytes` — OGG/Opus bytes (Opus magic header present); `tts.synthesize(text: str) -> bytes` (C5).
- `reply.send_voice(msg, ogg_bytes: bytes) -> Message | None` — best-effort voice reply; `None` on failure (text already delivered).
- Voice-in path yields either a routed turn (`_route_text(..., spoken=True)`) or a transcribed INBOX entry — never an untranscribed dump when text is present (C1).

## Invariants
- Heavy models (`faster_whisper`, `kokoro`) are lazy-imported INSIDE `stt._model()` / `tts._pipeline()`, never at module top: importing `stt`/`tts` must succeed with the deps uninstalled (C6).
- `stt.run` wraps transcription in try/except and returns `""` on ANY failure; empty and exception both collapse to `""` (C3).
- An empty transcript is NEVER dispatched: the voice branch guards on `t.strip()` and on empty falls back to transcribed→untranscribed INBOX + a `TRANSCRIBE_FAIL_PHRASES` notice (C3).
- The `spoken: bool` flag is kw-only with default `False`; text-triggered turns are byte-for-byte unaffected (C5). Voice reply is additive — its failure never blocks the already-delivered text.
- Voice transcripts route through the SAME `_route_text` as typed text (symmetry); the `"bot"` prefix is parsed by the existing `_strip_bot_prefix`, no new prefix logic (C2).

## Examples
Test coverage: `tests/test_stt.py` (C1 transcription success, C3 empty/exception), `tests/test_tts.py` (C5 OGG/Opus encode), `tests/test_route_text.py` (C2 "bot" prefix via spoken=True), `tests/test_hotwords.py` (C4 editable data), integration verified in `tests/test_reply_voice.py`.

- `stt.run(path, fake_model)` where `fake_model.transcribe` yields segments `["oi", " mundo"]` → `"oi mundo"`.
- `stt.run(path, raising_model)` (transcribe raises) → `""`; `stt.run(path, empty_model)` (no segments) → `""` (C3).
- `tts.encode_ogg(sine_wave_24k, 24000)` → non-empty `bytes` beginning with the OGG magic (`b"OggS"`), no model load (C5).
- Transcript `"bot roda os testes"` through `_route_text(spoken=True)` → `_strip_bot_prefix` → `_cmd_new` starts a new session (C2).
- Hotwords from `hotwords.as_prompt()` — workspace jargon list fed to faster-whisper's `hotwords=` (C4).

## Notes
- Provenance: `.loop/audio-in-out/` (3-arch.md architecture, 3b-contracts.md contracts). Corrected boundary: `inbox.save_media` is `async` and its real signature is `save_media(file_id: str, context, suffix: str) -> pathlib.Path` — the voice branch must `await inbox.save_media(voice.file_id, context, ".ogg")` before transcription (whisper needs the file on disk).
- `soundfile` is a top-level import (C6 installs it); only `faster_whisper`/`kokoro` are lazy.
- Sibling contracts: `dispatch.pyi`, `inbox.pyi`, `format.pyi`, `phrases.pyi` (existing frontend interfaces).
