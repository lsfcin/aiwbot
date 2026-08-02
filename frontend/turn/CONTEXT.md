# turn
> One message in, one answer out: read the intent, run the backend, put the answer on screen.
> spec: ../SPEC.md

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | — | — | **facade** — __init__.py — facade: one message in, one answer out: read the intent, run the backend, put the answer on screen. |
| [`directives.py`](directives.py) | — | `resolve` | directives.py — read leading harness/model words off a bot-prefixed message, no inference. |
| [`dispatch.py`](dispatch.py) | [`dispatch.pyi`](dispatch.pyi) | `TurnResult`, `DispatchError`, `join_texts`, `events_to_result`, `turn` | dispatch.py — one call site that drains any AgentBackend.send() into a single reply. |
| [`helpers.py`](helpers.py) | — | `friendly_error`, `transient`, `parse_new_arg`, `apply_directives`, `turn_options` | helpers.py — turn plumbing: friendly errors, /new arg parsing, sticky options, persistence. |
| [`runner.py`](runner.py) | — | `guarded`, `run_and_deliver`, `start_new`, `handle_reply_continue` | runner.py — run one turn and put its answer on screen: dispatch, deliver, anchor, speak. |
| [`startword.py`](startword.py) | — | `normalize`, `strip_prefix` | startword.py — does a message open with the "bot" session-start word, and what follows it. |
<!-- routing:end -->
