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
| [`format.py`](format.py) | [`format.pyi`](format.pyi) | `relative_time`, `plain`, `title_words`, `title_from_prompt`, `response_preview` | format.py — pure text formatting: markdown/tables -> Telegram HTML, session headers. No I/O. |
| [`inbox.py`](inbox.py) | [`inbox.pyi`](inbox.pyi) | `append_entry`, `build_entry`, `save_media` | inbox.py — capture plain text/media into brain/INBOX.md ($0, no backend call). |
| [`mode.py`](mode.py) | — | `toggle_markup`, `handle_callback` | mode.py — plan↔build segmented control: two footer buttons, selected one bracketed. Sticky/session. |
| [`phrases.py`](phrases.py) | [`phrases.pyi`](phrases.pyi) | `pick` | phrases.py — phrase banks (natural-language variants, picked at random per message) + help text. |
| [`reply.py`](reply.py) | — | `safe_reply`, `deliver` | reply.py — Telegram send primitives: safe reply, chunking, edit-in-place delivery. |
| [`resume.py`](resume.py) | — | `cmd_resume`, `handle_callback` | resume.py — /resume picker (Claude-Code-style): list recent sessions, tap to re-anchor + continue. |
| [`sessions.py`](sessions.py) | — | `remember`, `adopt`, `recent`, `count`, `backend_for` | sessions.py — session registry (backend/mode/reply_map, bot-only state) + cross-backend listing: |
<!-- routing:end -->
