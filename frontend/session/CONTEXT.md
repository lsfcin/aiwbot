# session
> Which session a message belongs to, and everything the bot remembers about it.
> spec: ../SPEC.md

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — facade: which session a message belongs to. Import session only through here. |
| [`anchor.py`](anchor.py) | `Anchors`, `note_session`, `add` | anchor.py — map each answer bubble to its session, so any of them can be replied to (AD-23). |
| [`msgmap.py`](msgmap.py) | `remember_reply`, `session_for_reply`, `remember_pending_new`, `pending_new`, `remember_ask` | msgmap.py — bounded message_id -> value maps: which session, which scope, which panel state. |
| [`registry.py`](registry.py) | `remember`, `adopt`, `defaults`, `setting_for`, `set_setting` | registry.py — bot-owned per-session state in config.json: knobs, titles, message maps. |
| [`resume.py`](resume.py) | `cmd_resume`, `handle_callback` | resume.py — /resume picker (Claude-Code-style): list recent sessions, tap to re-anchor + continue. |
| [`sessions.py`](sessions.py) | `recent`, `count`, `last_response` | sessions.py — cross-backend session listing: the /resume picker aggregates each backend's own |
<!-- routing:end -->
