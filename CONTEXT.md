# aiwbot
> Provider-agnostic bot: control swappable coding agents (claude·opencode·copilot) from chat.
> goal: [workspace-os](../../brain/goals/workspace-os.md)
> spec: none

## Overview
One `AgentBackend` interface normalizes every coding-agent CLI into a stream of `AgentEvent`s,
so the frontend (Telegram) never knows which provider runs underneath — provider is data, not code.
Phase A (current) proves the seam against claude + opencode with a bare harness + free fixture tests,
before any Telegram wiring.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`backend/`](backend/CONTEXT.md) | Provider-agnostic seam: each coding-agent CLI → normalized AgentEvent stream; one class per provider. |
| [`frontend/`](frontend/CONTEXT.md) | Telegram frontend on the AgentBackend seam — /new + reply-to-continue + INBOX capture. |
| [`tests/`](tests/CONTEXT.md) | Free unit tests — pure-logic fixtures/parsers/formatting, no network or cost. |

| File | Description |
|------|-------------|
| [`ISSUES.md`](ISSUES.md) | aiwbot — Issues |
| [`README.md`](README.md) | Provider-agnostic bot: drive swappable coding agents (claude · opencode · copilot) from chat. |
| [`REFS.md`](REFS.md) | aiwbot — References |
| [`ROADMAP-p2.md`](ROADMAP-p2.md) | aiwbot — P2: backend + model + effort selection |
| [`ROADMAP-p3.md`](ROADMAP-p3.md) | aiwbot — P3: Telegram output fidelity + `/resume` stability |
| [`ROADMAP.md`](ROADMAP.md) | aiwbot — Roadmap |
| [`SPECS-capability.md`](SPECS-capability.md) | What a backend declares it can do, and how mode, model and effort are offered. |
| [`SPECS-questions.md`](SPECS-questions.md) | An agent that asks: how the question is carried, positioned, and answered. |
| [`SPECS-seam.md`](SPECS-seam.md) | The one interface every coding-agent CLI becomes, and what it must pin. |
| [`SPECS-sessions.md`](SPECS-sessions.md) | Where a session lives, who can see it, and how a resume keeps one lineage. |
| [`SPECS-streaming.md`](SPECS-streaming.md) | How an answer arrives bubble by bubble, what is sealed, and what spend means. |
| [`SPECS-telegram.md`](SPECS-telegram.md) | Panels, buttons, tables and speech-to-text: what the chat client can render. |
| [`SPECS.md`](SPECS.md) | aiwbot — Specs |
| [`conftest.py`](conftest.py) | conftest.py — pytest anchor: puts the project root on sys.path so `backend` imports resolve. |
| [`proto.py`](proto.py) | proto.py — live smoke: run one prompt through each backend + prove single-lineage resume. ~$0.10/run. |
| [`requirements.txt`](requirements.txt) | requirements.txt — aiwbot's own additional runtime deps, installed into the shared workspace venv (/mnt/workspace/.venv) that already carries faster-whisper + ctranslate2 for other projects. Install: /mnt/workspace/.venv/bin/pip install -r requirements.txt /mnt/workspace/.venv/bin/pip install "numpy==2.4.5" --no-deps   # see NOTE below |
<!-- routing:end -->
