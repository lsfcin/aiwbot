# turn
> One message in, one answer out: triggers, directives, delivery, and INBOX capture.
> spec: none

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — marks tests/turn as a package. |
| [`test_bot.py`](test_bot.py) | — | test_bot.py — free unit test: "bot"-prefix trigger routing logic. |
| [`test_directives.py`](test_directives.py) | — | test_directives.py — F3a: read leading harness/model words off a bot-prefixed message, $0. |
| [`test_f2_papercuts.py`](test_f2_papercuts.py) | — | test_f2_papercuts.py — the F2 batch: phrase tone, flat glyphs, the reply anchor, and the |
| [`test_inbox.py`](test_inbox.py) | — | test_inbox.py — free unit test: build_entry tags forwarded (non-Lucas) captures. |
| [`test_route_text.py`](test_route_text.py) | `testrun_and_deliver_spoken_sends_voice_in_addition_to_text`, `testrun_and_deliver_not_spoken_never_sends_voice`, `fake_start_new`, `fake_reply_continue`, `fake_reply_continue` | test_route_text.py — free unit test: shared text/voice routing (_route_text), the C3 |
<!-- routing:end -->
