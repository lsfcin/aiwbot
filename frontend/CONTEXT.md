# frontend
> Telegram frontend on the AgentBackend seam — /new + reply-to-continue + INBOX capture.
> spec: none

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | — | — | **facade** — __init__.py — facade: Telegram frontend on the AgentBackend seam. Import frontend only through here. |
| [`bot.py`](bot.py) | — | `main` | bot.py — PTB wiring: allowlist, /new + reply-to-continue dispatch, plain text/media -> INBOX. |
| [`config.py`](config.py) | [`config.pyi`](config.pyi) | `config_dir`, `load_config`, `save_config`, `bot_token`, `allowed_chat_id` | config.py — aiwbot's own Telegram config dir (separate token/storage from the old workspace bot). |
| [`dispatch.py`](dispatch.py) | [`dispatch.pyi`](dispatch.pyi) | `TurnResult`, `DispatchError`, `events_to_result`, `turn` | dispatch.py — one call site that drains any AgentBackend.send() into a single reply. |
| [`format.py`](format.py) | [`format.pyi`](format.pyi) | `plain`, `title_words`, `format_body`, `session_block` | format.py — pure text formatting: markdown/tables -> Telegram HTML, session headers. No I/O. |
| [`inbox.py`](inbox.py) | [`inbox.pyi`](inbox.pyi) | `append_entry`, `build_entry`, `save_media` | inbox.py — capture plain text/media into brain/INBOX.md ($0, no backend call). |
| [`phrases.py`](phrases.py) | [`phrases.pyi`](phrases.pyi) | `pick` | phrases.py — phrase banks (natural-language variants, picked at random per message) + help text. |
| [`sessions.py`](sessions.py) | — | `remember`, `backend_for`, `remember_reply`, `session_for_reply` | sessions.py — local registry: session_id -> backend (no cross-backend `agents --json` equivalent |
<!-- routing:end -->
