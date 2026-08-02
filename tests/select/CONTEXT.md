# select
> The picker keyboards: which grid a tap opens, and what one tap costs.
> spec: none

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — marks tests/select as a package. |
| [`test_f3c_tap_latency.py`](test_f3c_tap_latency.py) | `answer`, `edit_message_reply_markup`, `capabilities`, `efforts` | test_f3c_tap_latency.py — F3c: a panel tap costs ONE Telegram round trip, not two or three. |
| [`test_panel.py`](test_panel.py) | `answer`, `edit_message_reply_markup` | test_panel.py — free unit test: panel effects — scopes, applying a choice, hidden dims. |
| [`test_panelmenu.py`](test_panelmenu.py) | — | test_panelmenu.py — free unit test: panel layout — rows, controls, ordering, paging. |
<!-- routing:end -->
