# stream
> The answer arriving live: deltas, repaint rate, and bubbles sealed as they are born.
> spec: none

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — marks tests/stream as a package. |
| [`test_f4_frames.py`](test_f4_frames.py) | — | test_f4_frames.py — F4 Stage 2: what may be RENDERED mid-stream, and the guarantee that a |
| [`test_f4_sealing.py`](test_f4_sealing.py) | `go`, `go` | test_f4_sealing.py — F4 Stage 3: bubbles sealed as they are born, and the property that makes |
| [`test_f4_streaming.py`](test_f4_streaming.py) | `send_action`, `edit_text`, `run`, `run`, `timed` | test_f4_streaming.py — F4 Stage 2: the live bubble. Throttle mechanics, the pin, and the |
| [`test_f5_answer_shape.py`](test_f5_answer_shape.py) | `reply_text` | test_f5_answer_shape.py — F5: a long answer arrives as several repliable bubbles. |
| [`test_f6_bubble_shape.py`](test_f6_bubble_shape.py) | `go`, `go`, `go` | test_f6_bubble_shape.py — the furniture on a bubble, decided by Lucas on 2026-07-28: the voice |
| [`test_f6_pacing.py`](test_f6_pacing.py) | `timed`, `run` | test_f6_pacing.py — the pause BETWEEN bubbles (Lucas, 2026-07-28). Distinct from the repaint |
| [`test_stream_parse.py`](test_stream_parse.py) | `consume` | test_stream_parse.py — F4 Stage 1: claude's stream-json becomes deltas, and the turn still |
<!-- routing:end -->
