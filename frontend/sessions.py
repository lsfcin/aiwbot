# sessions.py — local registry: session_id -> backend (no cross-backend `agents --json` equivalent
# exists, so the frontend must remember this itself) + reply_map (message_id -> session_id).
from __future__ import annotations
import time
from . import config

REPLY_MAP_MAX = 50


def remember(session_id: str, backend: str, title: str | None = None, preview: str | None = None) -> None:
    cfg = config.load_config()
    sessions = cfg.get("sessions", {})
    now = time.time()
    sessions[session_id] = {"backend": backend, "title": title, "preview": preview, "updated_at": now}
    config.save_config(sessions=sessions)


def _matches(entry: dict, query: str) -> bool:
    title = entry.get("title") or ""
    lowered = title.lower()
    return (not query) or (query in lowered)


def recent(n: int, query: str = "") -> list[dict]:
    """Sessions newest-first (optionally filtered by title substring) for the /resume picker.

    Untitled entries (saved before the title feature shipped) are ghosts — skip them."""
    sessions = config.load_config().get("sessions", {})
    q = query.lower()
    items = []
    for sid, entry in sessions.items():
        if not entry.get("title"):
            continue
        if not _matches(entry, q):
            continue
        item = {"session_id": sid, "backend": entry.get("backend"), "title": entry.get("title"),
                "preview": entry.get("preview"), "updated_at": entry.get("updated_at", 0)}
        items.append(item)
    items.sort(key=lambda e: e["updated_at"], reverse=True)
    return items[:n]


def count(query: str = "") -> int:
    sessions = config.load_config().get("sessions", {})
    q = query.lower()
    total = 0
    for entry in sessions.values():
        if not entry.get("title"):
            continue
        if _matches(entry, q):
            total += 1
    return total


def backend_for(session_id: str) -> str | None:
    sessions = config.load_config().get("sessions", {})
    entry = sessions.get(session_id, {})
    return entry.get("backend")


def title_for(session_id: str) -> str | None:
    sessions = config.load_config().get("sessions", {})
    entry = sessions.get(session_id, {})
    return entry.get("title")


def mode_for(session_id: str) -> str:
    """Sticky per-session mode ∈ {build, plan}; defaults to build when unset."""
    sessions = config.load_config().get("sessions", {})
    entry = sessions.get(session_id, {})
    return entry.get("mode") or "build"


def set_mode(session_id: str, mode: str) -> None:
    """Persist the session's mode, preserving the rest of its registry entry."""
    cfg = config.load_config()
    sessions = cfg.get("sessions", {})
    entry = sessions.get(session_id)
    if entry is not None:
        entry["mode"] = mode
        config.save_config(sessions=sessions)


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
