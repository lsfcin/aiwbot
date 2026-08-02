# interview
> The agent asking Lucas a question mid-turn: the broker, its transport, and the bubble it draws.
> spec: ../SPEC.md

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — facade: the agent asking Lucas a question mid-turn: the broker, its transport, and the bubble it draws. |
| [`ask.py`](ask.py) | `new_token`, `register`, `unregister`, `question_of`, `answer` | ask.py — the bot side of ask_user: hold a running turn open on a question until Lucas answers. |
| [`askserver.py`](askserver.py) | `url`, `port`, `handle_rpc`, `start` | askserver.py — the daemon's own MCP server: one HTTP endpoint per live turn, JSON-RPC by hand. |
| [`askshape.py`](askshape.py) | `markup`, `bubble_text`, `answer_note`, `close` | askshape.py — what a question LOOKS like in the chat: its bubble, its keys, and how it closes. |
<!-- routing:end -->
