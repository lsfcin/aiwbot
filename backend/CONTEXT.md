# backend
> ← add description

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | — | `get_backend`, `backend_names` | **facade** — __init__.py — facade: seam types + backend registry. Import backends only through here. |
| [`base.py`](base.py) | — | `AgentEvent`, `TurnOptions`, `AgentBackend`, `try_json`, `check_contract` | base.py — the provider-agnostic seam: AgentEvent + AgentBackend contract + shared primitives. |
| [`claude.py`](claude.py) | — | `parse_events`, `ClaudeBackend`, `build_args`, `parse`, `list_sessions` | claude.py — ClaudeBackend: normalizes `claude -p --output-format json` (single result object). |
| [`cli.py`](cli.py) | — | `CliBackend`, `build_args`, `parse`, `list_sessions`, `send` | cli.py — CliBackend: the single subprocess-driven send() loop; subclasses supply build_args + parse. |
| [`opencode.py`](opencode.py) | — | `parse_events`, `OpencodeBackend`, `build_args`, `parse`, `list_sessions` | opencode.py — OpencodeBackend: normalizes `opencode run --format json` (JSONL stream). |
| [`proc.py`](proc.py) | — | `run_capture`, `events_from_run` | proc.py — subprocess driver + run-result → events handling (shared by all CLI backends). |
| [`transcript.py`](transcript.py) | — | `tail_lines`, `latest_ai_title`, `last_response_text`, `last_model` | transcript.py — read a claude .jsonl transcript from the tail for title/preview/context %. |
<!-- routing:end -->
