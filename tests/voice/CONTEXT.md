# voice
> The audio-in-out pipeline: transcribe in, speak out, and what the chat says while it listens.
> spec: none

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — marks tests/voice as a package. |
| [`test_f6_voice_feedback.py`](test_f6_voice_feedback.py) | `fake_save`, `fake_route`, `fake_edit`, `fake_safe_reply`, `fake_turn` | test_f6_voice_feedback.py — a voice note says something back before it has been transcribed |
| [`test_hotwords.py`](test_hotwords.py) | — | test_hotwords.py — free unit test: hotwords is explicit editable data (C4), not inline in stt.py. |
| [`test_reply_voice.py`](test_reply_voice.py) | `FakeMsg`, `FailingMsg`, `reply_voice`, `reply_voice` | test_reply_voice.py — free unit test: reply.send_voice (C5), mirrors safe_reply's Telegram-error |
| [`test_speech.py`](test_speech.py) | — | test_speech.py — free unit test: markdown answer -> prose a TTS voice can read (F3b). |
| [`test_stt.py`](test_stt.py) | `FakeSegment`, `FakeModel`, `transcribe`, `BoomModel`, `transcribe` | test_stt.py — free unit test: STT wrapper (C1 transcription, C3 fail-safe, C6 no live calls). |
| [`test_tts.py`](test_tts.py) | `FakePipeline` | test_tts.py — free unit test: TTS wrapper (C5 voice reply) + local OGG/Opus encode (C6, no live calls). |
| [`test_voice_echo_and_picker.py`](test_voice_echo_and_picker.py) | — | test_voice_echo_and_picker.py — Lucas's 2026-07-27 live test: STT conditioning prompt shape, |
<!-- routing:end -->
