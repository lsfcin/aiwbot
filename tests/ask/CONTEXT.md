# ask
> The agent interviewing Lucas mid-turn: the broker, the transport, and the chat it draws.
> spec: none

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — marks tests/ask as a package. |
| [`test_f4_ask.py`](test_f4_ask.py) | `go`, `go`, `go`, `go`, `go` | test_f4_ask.py — F4 Stage 4: the broker. One asyncio.Future per question, the chat UX that |
| [`test_f4_ask_wiring.py`](test_f4_ask_wiring.py) | — | test_f4_ask_wiring.py — F4 Stage 4: the transport and the CLI wiring around the broker. |
| [`test_f6_interview_shape.py`](test_f6_interview_shape.py) | `go` | test_f6_interview_shape.py — what the chat looks like when the agent interviews Lucas mid-turn |
| [`test_f7_opencode_ask.py`](test_f7_opencode_ask.py) | — | test_f7_opencode_ask.py — opencode parity: the ask transport and the retry vocabulary. |
| [`test_f8_ask_answer_shape.py`](test_f8_ask_answer_shape.py) | `go`, `answer_now`, `answer_now`, `tap_second`, `answer_now` | test_f8_ask_answer_shape.py — what an interview looks like in the chat, from Lucas reading a real |
<!-- routing:end -->
