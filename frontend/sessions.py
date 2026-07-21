# sessions.py — local registry: session_id -> backend (no cross-backend `agents --json` equivalent
# exists, so the frontend must remember this itself) + reply_map (message_id -> session_id).
from __future__ import annotations
from . import config

REPLY_MAP_MAX = 50


def remember(session_id: str, backend: str, title: str | None = None) -> None:
    cfg = config.load_config()
    sessions = cfg.get("sessions", {})
    sessions[session_id] = {"backend": backend, "title": title}
    config.save_config(sessions=sessions)


def backend_for(session_id: str) -> str | None:
    sessions = config.load_config().get("sessions", {})
    entry = sessions.get(session_id, {})
    return entry.get("backend")


def remember_reply(message_id: int, session_id: str) -> None:
    cfg = config.load_config()
    reply_map = cfg.get("reply_map", {})
    reply_map[str(message_id)] = session_id
    if len(reply_map) > REPLY_MAP_MAX:
        stale = sorted(reply_map, key=int)[: len(reply_map) - REPLY_MAP_MAX]
        for k in stale:
            del reply_map[k]
    config.save_config(reply_map=reply_map)


def session_for_reply(message_id: int) -> str | None:
    reply_map = config.load_config().get("reply_map", {})
    return reply_map.get(str(message_id))
