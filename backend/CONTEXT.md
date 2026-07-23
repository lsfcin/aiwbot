# backend
> Provider-agnostic seam: each coding-agent CLI → normalized AgentEvent stream; one class per provider.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | — | `get_backend`, `backend_names` | **facade** — __init__.py — facade: seam types + backend registry. Import backends only through here. |
| [`base.py`](base.py) | — | `AgentEvent`, `TurnOptions`, `add_flag`, `AgentBackend`, `try_json` | base.py — the provider-agnostic seam: AgentEvent + AgentBackend contract + shared primitives. |
| [`caps.py`](caps.py) | — | `Capabilities` | caps.py — capability declaration: what modes/models a backend may actually be offered. |
| [`catalog.py`](catalog.py) | — | `metadata`, `efforts`, `context_window`, `model_ids`, `groups` | catalog.py — opencode's model catalogue: configured ids + per-model effort/context metadata. |
| [`claude.py`](claude.py) | — | `parse_events`, `ClaudeBackend`, `build_args`, `capabilities`, `efforts` | claude.py — ClaudeBackend: normalizes `claude -p --output-format json` (single result object). |
| [`cli.py`](cli.py) | — | `CliBackend`, `build_args`, `parse`, `list_sessions`, `last_response` | cli.py — CliBackend: the single subprocess-driven send() loop; subclasses supply build_args + parse. |
| [`ocstore.py`](ocstore.py) | — | `session_rows`, `model_of`, `context_used`, `last_turn` | ocstore.py — read-only reads of opencode's sqlite store: session rows + last assistant answer. |
| [`opencode.py`](opencode.py) | — | `parse_events`, `OpencodeBackend`, `build_args`, `parse`, `capabilities` | opencode.py — OpencodeBackend: normalizes `opencode run --format json` (JSONL stream). |
| [`proc.py`](proc.py) | — | `run_capture`, `events_from_run` | proc.py — subprocess driver + run-result → events handling (shared by all CLI backends). |
| [`transcript.py`](transcript.py) | — | `tail_lines`, `latest_ai_title`, `last_response_text`, `last_context_used`, `last_model` | transcript.py — read a claude .jsonl transcript from the tail for title/preview/context %. |
<!-- routing:end -->
