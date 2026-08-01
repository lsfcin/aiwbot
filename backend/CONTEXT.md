# backend
> Provider-agnostic seam: each coding-agent CLI → normalized AgentEvent stream; one class per provider.

## Shape — the root is provider-agnostic, `providers/` is where a provider's name may appear

Split 2026-08-01 at 12 files. The root holds only what every backend shares and no provider
owns: the seam contract (`base`, `caps`), the single subprocess-driven `send()` loop (`cli`),
and the plumbing under it (`proc`, `binaries`). **A file at this level that names claude or
opencode is in the wrong directory** — that is the whole point of the boundary, and it is
cheaper to see as a path than to enforce by review.

`providers/` holds one class per CLI plus the records that CLI keeps for itself: claude's
stream parser and `.jsonl` transcript, opencode's sqlite store and model catalogue. The
registry that maps a name to a class stays in this facade, so adding a provider touches
`providers/` and one line here.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`providers/`](providers/CONTEXT.md) | One class per coding-agent CLI, plus the records that CLI keeps: its parser, its |

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | `get_backend`, `backend_names` | **facade** — __init__.py — facade: seam types + backend registry. Import backends only through here. |
| [`base.py`](base.py) | `AgentEvent`, `TurnOptions`, `add_flag`, `AgentBackend`, `try_json` | base.py — the provider-agnostic seam: AgentEvent + AgentBackend contract + shared primitives. |
| [`binaries.py`](binaries.py) | `resolve`, `find` | binaries.py — resolve a CLI's executable: PATH first, then the places its installer puts it. |
| [`caps.py`](caps.py) | `Capabilities` | caps.py — capability declaration: what modes/models a backend may actually be offered. |
| [`cli.py`](cli.py) | `CliBackend`, `build_args`, `parse`, `list_sessions`, `last_response` | cli.py — CliBackend: the single subprocess-driven send() loop; subclasses supply build_args + parse. |
| [`proc.py`](proc.py) | `run_capture`, `child_env`, `stream_lines`, `silent_run`, `events_from_run` | proc.py — subprocess driver + run-result → events handling (shared by all CLI backends). |
<!-- routing:end -->
