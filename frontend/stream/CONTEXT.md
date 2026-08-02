# stream
> The answer arriving live: which bubbles are open, when they may move, and how they land.
> spec: ../SPEC.md

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — facade: the answer arriving live: which bubbles are open, when they may move, and how they land. |
| [`answer.py`](answer.py) | `quote`, `decorate`, `room`, `bare_frames`, `frames` | answer.py — the shape of one answer message: the agent's text, then the footer that names it. |
| [`bubbles.py`](bubbles.py) | `Bubbles`, `write`, `open`, `cut`, `discard` | bubbles.py — the messages one answer is written into: which are live, which are sealed, and what |
| [`cadence.py`](cadence.py) | `Cadence`, `due`, `spaced`, `typing_due`, `mark_paint` | cadence.py — when a streamed answer is allowed to move: repaint rate, typing, bubble spacing. |
| [`landing.py`](landing.py) | `land`, `stamp` | landing.py — turn the live bubbles into the finished answer: the footer, the keyboard, and the |
| [`painter.py`](painter.py) | `Painter`, `sent`, `answers`, `note_session`, `frames` | painter.py — keep the chat showing the answer as it arrives, throttled. One object per turn. |
<!-- routing:end -->
