# sessions.py — session registry (backend/mode/reply_map, bot-only state) + cross-backend listing:
# the /resume picker aggregates each backend's own store so it sees VSCode sessions too, not just ours.
from __future__ import annotations
import time
from backend import get_backend, backend_names
from . import config

REPLY_MAP_MAX = 50


def remember(session_id: str, backend: str, title: str | None = None, preview: str | None = None) -> None:
    cfg = config.load_config()
    sessions = cfg.get("sessions", {})
    now = time.time()
    sessions[session_id] = {"backend": backend, "title": title, "preview": preview, "updated_at": now}
    config.save_config(sessions=sessions)


def adopt(session_id: str, backend: str, title: str | None, updated_at: float) -> None:
    """Cache a store-listed session's backend/title into the registry (preserving any existing
    mode/preview) so anchor + reply-to-continue resolve it — even VSCode sessions we didn't create."""
    cfg = config.load_config()
    sessions = cfg.get("sessions", {})
    entry = sessions.get(session_id, {})
    entry["backend"] = backend
    entry["title"] = title
    entry["updated_at"] = updated_at
    entry.setdefault("preview", None)
    sessions[session_id] = entry
    config.save_config(sessions=sessions)


def remember_context_window(model: str | None, window: int | None) -> None:
    """Learn a model's context window from a live turn. Transcripts don't record it, so the
    /resume list reuses what we've observed instead of hardcoding per-model constants."""
    if model and window:
        cfg = config.load_config()
        windows = cfg.get("context_windows", {})
        windows[model] = window
        config.save_config(context_windows=windows)


def context_window_for(model: str | None) -> int | None:
    """Observed context window for a model, or None if we've never seen a live turn on it."""
    windows = config.load_config().get("context_windows", {})
    return windows.get(model or "")


def _title_matches(title: str | None, query: str) -> bool:
    lowered = (title or "").lower()
    return (not query) or (query in lowered)


def _all(cwd: str) -> list[dict]:
    """Every resumable session for cwd, aggregated across backends, each tagged with its backend."""
    items: list[dict] = []
    for name in backend_names():
        backend = get_backend(name)
        listed = backend.list_sessions(cwd)
        for item in listed:
            item["backend"] = name
            items.append(item)
    items.sort(key=lambda e: e["updated_at"], reverse=True)
    return items


def recent(n: int, query: str, cwd: str, offset: int = 0) -> list[dict]:
    """Newest-first sessions (optionally title-filtered) for the /resume picker, from the backend
    stores. Adopts each shown session into the registry so a later tap can resolve backend+title.
    offset paginates: the picker shows one page at a time behind ‹ / › buttons."""
    q = query.lower()
    items = []
    for item in _all(cwd):
        if not _title_matches(item.get("title"), q):
            continue
        item.setdefault("preview", None)
        items.append(item)
    page = items[offset:offset + n]
    for item in page:
        sid = item["session_id"]
        adopt(sid, item["backend"], item.get("title"), item["updated_at"])
        item["mode"] = mode_for(sid)
        item["context_window"] = context_window_for(item.get("model"))
    return page


def count(query: str, cwd: str) -> int:
    q = query.lower()
    total = 0
    for item in _all(cwd):
        if _title_matches(item.get("title"), q):
            total += 1
    return total


def backend_for(session_id: str) -> str | None:
    sessions = config.load_config().get("sessions", {})
    entry = sessions.get(session_id, {})
    return entry.get("backend")


def last_response(session_id: str, cwd: str) -> str:
    """Full text of the session's last answer, from whichever backend owns it."""
    name = backend_for(session_id)
    text = ""
    if name:
        backend = get_backend(name)
        text = backend.last_response(session_id, cwd)
    return text


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


def _remember_by_message(map_name: str, message_id: int, value: str) -> None:
    """Bounded message_id -> value map (oldest ids evicted first). Shared by the
    reply-to-continue map and the pending-/new map."""
    cfg = config.load_config()
    mapping = cfg.get(map_name, {})
    mapping[str(message_id)] = value
    if len(mapping) > REPLY_MAP_MAX:
        stale = sorted(mapping, key=int)[: len(mapping) - REPLY_MAP_MAX]
        for k in stale:
            del mapping[k]
    config.save_config(**{map_name: mapping})


def _value_by_message(map_name: str, message_id: int) -> str | None:
    mapping = config.load_config().get(map_name, {})
    return mapping.get(str(message_id))


def remember_reply(message_id: int, session_id: str) -> None:
    _remember_by_message("reply_map", message_id, session_id)


def session_for_reply(message_id: int) -> str | None:
    return _value_by_message("reply_map", message_id)


def remember_pending_new(message_id: int, backend: str) -> None:
    """A /new with no prompt asks for one via ForceReply; the answer to THAT message
    is the prompt, so remember which backend the pending session should use."""
    _remember_by_message("pending_new", message_id, backend)


def pending_new(message_id: int) -> str | None:
    return _value_by_message("pending_new", message_id)
