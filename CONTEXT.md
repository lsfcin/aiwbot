# aiwbot
> Provider-agnostic bot: control swappable coding agents (claude·opencode·copilot) from chat.
> goal: [workspace-os](../../brain/goals/workspace-os.md)
> spec: none

## Overview
One `AgentBackend` interface normalizes every coding-agent CLI into a stream of `AgentEvent`s,
so the frontend (Telegram) never knows which provider runs underneath — provider is data, not code.
Phase A (current) proves the seam against claude + opencode with a bare harness + free fixture tests,
before any Telegram wiring. Reuses plumbing from the workspace bot (core/tools/telegram_daemon.py).

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`backend/`](backend/CONTEXT.md) | Provider-agnostic seam: each coding-agent CLI → normalized AgentEvent stream; on |
| [`frontend/`](frontend/CONTEXT.md) | Telegram frontend on the AgentBackend seam — /new + reply-to-continue + INBOX ca |
| [`tests/`](tests/CONTEXT.md) | Free unit tests — pure-logic fixtures/parsers/formatting, no network or cost. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`HISTORY.md`](HISTORY.md) | — | — | aiwbot — History |
| [`KNOWN-BUGS.md`](KNOWN-BUGS.md) | — | — | aiwbot — Known Bugs |
| [`README.md`](README.md) | — | — | aiwbot |
| [`REFS.md`](REFS.md) | — | — | aiwbot — References |
| [`ROADMAP.md`](ROADMAP.md) | — | — | aiwbot — Roadmap |
| [`SPECS.md`](SPECS.md) | — | — | aiwbot — Specs |
| [`conftest.py`](conftest.py) | — | — | conftest.py — pytest anchor: puts the project root on sys.path so `backend` imports resolve. |
| [`proto.py`](proto.py) | — | — | proto.py — live smoke: run one prompt through each backend + prove single-lineage resume. ~$0.10/run. |
<!-- routing:end -->
