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

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`backend/__init__.py`](backend/__init__.py) | — | `get_backend` | **facade** — __init__.py — facade: seam types + backend registry. Import backends only through here. |
| [`tests/__init__.py`](tests/__init__.py) | — | — | **facade** — __init__.py — marks tests as a package. |
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
| [`tests/test_dispatch.py`](tests/test_dispatch.py) | — | `test_claude_fixture_consolidates_to_result`, `test_opencode_fixture_consolidates_to_result`, `test_error_event_raises_dispatch_error`, `test_missing_result_event_raises_dispatch_error` | test_dispatch.py — free unit test: AgentEvent list -> TurnResult, using Phase A fixtures. |
| [`tests/test_format.py`](tests/test_format.py) | — | `test_plain_markdown_to_html`, `test_pipe_table_boxed_as_pre`, `test_fenced_code_block_boxed_as_pre`, `test_title_words_defaults_when_empty`, `test_session_block_includes_header_and_body` | test_format.py — free unit test: markdown/table -> Telegram HTML conversion. |
| [`tests/test_parse_claude.py`](tests/test_parse_claude.py) | — | `test_claude_has_text_and_result`, `test_claude_text_and_session`, `test_claude_contract`, `test_resume_is_single_lineage_no_fork` | test_parse_claude.py — free unit test: claude fixture -> normalized AgentEvents satisfy the contract. |
| [`tests/test_parse_opencode.py`](tests/test_parse_opencode.py) | — | `test_opencode_has_text_and_result`, `test_opencode_text_and_session`, `test_opencode_contract` | test_parse_opencode.py — free unit test: opencode JSONL fixture -> AgentEvents satisfy the contract. |
<!-- routing:end -->
