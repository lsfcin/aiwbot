# tests
> Free unit tests — pure-logic fixtures/parsers/formatting, no network or cost.
> spec: none

## Shape — the root holds the kits, every subdirectory holds one subject

Split 2026-08-01 at 51 files in one flat directory. Only the shared scaffolding stays at the
root: `conftest.py` and the three kits (`chatkit` Telegram fakes, `panelkit` keyboard readers,
`streamkit` async-stream fakes). Everything else routes through the table below, grouped by
*what it asserts*, not by which release named it — a `test_f6_*` file sits with the behaviour it
pins, so a bug in the live bubble is one directory to read, not a grep across the whole suite.

Two directories cover the backend seam (`seam/`, `store/`); the other six mirror the frontend's
own responsibilities, so a source directory and its tests carry the same name.

A subdirectory under `WARN_FILES` folds back into this table unless it carries its own
`CONTEXT.md`, so each one declares itself and this table went 51 rows → 12. Moving files
without paying that cost would satisfy the fanout count while leaving the reader exactly as
much to hold.

**Scaffolding is imported from a kit, never from a sibling test.** `FakeMsg`/`FakeReplyAnchor`
lived in `test_route_text.py` and were imported by a voice test; the split turned that into a
cross-directory import and they moved to `chatkit.py`, where they belonged.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`ask/`](ask/CONTEXT.md) | The agent interviewing Lucas mid-turn: the broker, the transport, and the chat i |
| [`seam/`](seam/CONTEXT.md) | The AgentBackend seam: a CLI's output becomes AgentEvents, and a turn's options  |
| [`select/`](select/CONTEXT.md) | Choosing the target — harness, model, effort, session — and remembering the choi |
| [`store/`](store/CONTEXT.md) | What a provider already wrote: its session store, its transcript, its model cata |
| [`stream/`](stream/CONTEXT.md) | The answer arriving live: deltas, repaint rate, and bubbles sealed as they are b |
| [`text/`](text/CONTEXT.md) | Agent markdown becomes Telegram HTML: blocks, inline spans, tables, chunking, bu |
| [`turn/`](turn/CONTEXT.md) | One message in, one answer out: triggers, directives, delivery, and INBOX captur |
| [`voice/`](voice/CONTEXT.md) | The audio-in-out pipeline: transcribe in, speak out, and what the chat says whil |

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — marks tests as a package. |
| [`chatkit.py`](chatkit.py) | `Bubble`, `Chat`, `FakeReplyAnchor`, `FakeMsg`, `Origin` | chatkit.py — shared Telegram fakes: a chat that records every write, its bubbles, and the |
| [`conftest.py`](conftest.py) | `store` | conftest.py — fixtures shared by the panel tests: an in-memory config and a fake backend. |
| [`panelkit.py`](panelkit.py) | `Fake`, `labels`, `texts`, `data`, `capabilities` | panelkit.py — shared panel-test scaffolding: a fake backend plus keyboard readers. |
| [`streamkit.py`](streamkit.py) | `deltas`, `result`, `FakeStream`, `Clock`, `send` | streamkit.py — shared streaming-test scaffolding: an async-generator fake backend and a clock. |
<!-- routing:end -->
