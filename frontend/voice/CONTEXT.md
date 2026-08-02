# voice
> The audio-in-out pipeline: what the bot hears, and what it says back.
> spec: ../SPEC.md

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — facade: the audio-in-out pipeline: what the bot hears, and what it says back. |
| [`hotwords.py`](hotwords.py) | `as_prompt` | hotwords.py — explicit editable data (C4): what the STT is primed with before it listens. |
| [`speech.py`](speech.py) | `to_speech` | speech.py — an agent's markdown answer -> prose a TTS voice can actually read aloud. |
| [`stt.py`](stt.py) | `confident`, `run`, `transcribe` | stt.py — STT wrapper: faster-whisper large-v3-turbo, lazy-loaded; fails safe to "" (C1, C3). |
| [`tts.py`](tts.py) | `encode_ogg`, `synthesize` | tts.py — TTS wrapper: Kokoro-82M pf_dora voice, lazy-loaded; local OGG/Opus encode (C5, C6). |
<!-- routing:end -->
