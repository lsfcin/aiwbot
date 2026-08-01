# select
> Choosing the target — harness, model, effort, session — and remembering the choice.
> spec: none

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — marks tests/select as a package. |
| [`test_f3c_tap_latency.py`](test_f3c_tap_latency.py) | `answer`, `edit_message_reply_markup`, `capabilities`, `efforts` | test_f3c_tap_latency.py — F3c: a panel tap costs ONE Telegram round trip, not two or three. |
| [`test_panel.py`](test_panel.py) | `answer`, `edit_message_reply_markup` | test_panel.py — free unit test: panel effects — scopes, applying a choice, hidden dims. |
| [`test_panelmenu.py`](test_panelmenu.py) | — | test_panelmenu.py — free unit test: panel layout — rows, controls, ordering, paging. |
| [`test_registry.py`](test_registry.py) | `store` | test_registry.py — free unit test: scopes (session vs NEW), last-used defaults, message maps. |
| [`test_resume.py`](test_resume.py) | — | test_resume.py — free unit test: /resume picker list/label/pagination assembly. |
| [`test_sessions.py`](test_sessions.py) | `two_backends`, `list_sessions`, `session_detail` | test_sessions.py — free unit test: cross-backend /resume aggregation + registry adopt/mode. |
<!-- routing:end -->
