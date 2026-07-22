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
| [`frontend/`](frontend/CONTEXT.md) | Telegram frontend on the AgentBackend seam — /new + reply-to-continue + INBOX ca |
| [`tests/`](tests/CONTEXT.md) | Free unit tests — pure-logic fixtures/parsers/formatting, no network or cost. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`backend/__init__.py`](backend/__init__.py) | — | `get_backend` | **facade** — __init__.py — facade: seam types + backend registry. Import backends only through here. |
| [`HISTORY.md`](HISTORY.md) | — | — | aiwbot — History |
| [`KNOWN-BUGS.md`](KNOWN-BUGS.md) | — | — | aiwbot — Known Bugs |
| [`README.md`](README.md) | — | — | aiwbot |
| [`ROADMAP.md`](ROADMAP.md) | — | — | aiwbot — Roadmap |
| [`SPECS.md`](SPECS.md) | — | — | aiwbot — Specs |
| [`backend/base.py`](backend/base.py) | — | `AgentEvent`, `AgentBackend`, `try_json`, `check_contract`, `send` | base.py — the provider-agnostic seam: AgentEvent + AgentBackend contract + shared primitives. |
| [`backend/claude.py`](backend/claude.py) | — | `parse_events`, `ClaudeBackend`, `build_args`, `parse` | claude.py — ClaudeBackend: normalizes `claude -p --output-format json` (single result object). |
| [`backend/cli.py`](backend/cli.py) | — | `CliBackend`, `build_args`, `parse`, `send` | cli.py — CliBackend: the single subprocess-driven send() loop; subclasses supply build_args + parse. |
| [`backend/opencode.py`](backend/opencode.py) | — | `parse_events`, `OpencodeBackend`, `build_args`, `parse` | opencode.py — OpencodeBackend: normalizes `opencode run --format json` (JSONL stream). |
| [`backend/proc.py`](backend/proc.py) | — | `run_capture`, `events_from_run` | proc.py — subprocess driver + run-result → events handling (shared by all CLI backends). |
| [`conftest.py`](conftest.py) | — | — | conftest.py — pytest anchor: puts the project root on sys.path so `backend` imports resolve. |
| [`proto.py`](proto.py) | — | — | proto.py — live smoke: run one prompt through each backend + prove single-lineage resume. ~$0.10/run. |
<!-- routing:end -->
