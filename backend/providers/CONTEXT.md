# providers
> One class per coding-agent CLI, plus the records that CLI keeps: its parser, its store, its catalogue.
> spec: none

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — facade: the concrete backends. Registered in backend/__init__.py, not here. |
| [`catalog.py`](catalog.py) | `metadata`, `efforts`, `context_window`, `model_ids`, `groups` | catalog.py — opencode's model catalogue: configured ids + per-model effort/context metadata. |
| [`claude.py`](claude.py) | `ClaudeBackend`, `build_args`, `capabilities`, `efforts`, `last_response` | claude.py — ClaudeBackend: normalizes `claude -p --output-format json` (single result object). |
| [`claudeparse.py`](claudeparse.py) | `parse_events`, `StreamParser`, `feed`, `finish` | claudeparse.py — claude's output → AgentEvents, both shapes: one result object, and stream-json. |
| [`ocstore.py`](ocstore.py) | `session_rows`, `recent_models`, `model_of`, `context_used`, `last_model` | ocstore.py — read-only reads of opencode's sqlite store: session rows + last assistant answer. |
| [`opencode.py`](opencode.py) | `parse_events`, `LineStream`, `OpencodeBackend`, `feed`, `finish` | opencode.py — OpencodeBackend: normalizes `opencode run --format json` (JSONL stream). |
| [`transcript.py`](transcript.py) | `tail_lines`, `latest_ai_title`, `last_response_text`, `last_context_used`, `last_model` | transcript.py — read a claude .jsonl transcript from the tail for title/preview/context %. |
<!-- routing:end -->
