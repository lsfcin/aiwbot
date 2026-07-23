# registry.py — bot-owned per-session state in config.json: knobs, titles, message maps.
# Side-state only: the provider stores stay the source of truth for what sessions exist (AD-6).
from __future__ import annotations
import time
from . import config

REPLY_MAP_MAX = 50
DEFAULT_BACKEND = "claude"
DEFAULT_MODE = "build"


def _entries() -> dict:
    return config.load_config().get("sessions", {})


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


def setting_for(session_id: str, key: str, default: str | None = None) -> str | None:
    """One sticky per-session knob (mode/model/effort). Unset reads as the default, which is
    how "let the provider decide" stays distinct from a value that was actually picked."""
    entry = _entries().get(session_id, {})
    return entry.get(key) or default


def set_setting(session_id: str, key: str, value: str | None) -> None:
    """Persist one knob, preserving the rest of the entry. Unknown sessions are ignored on
    purpose: every message carrying a panel was remembered or adopted first, so a write
    against an unknown id means a stale keyboard, not a new session."""
    cfg = config.load_config()
    sessions = cfg.get("sessions", {})
    entry = sessions.get(session_id)
    if entry is not None:
        entry[key] = value
        config.save_config(sessions=sessions)


def backend_for(session_id: str) -> str | None:
    """The provider that owns this lineage — the one that can actually resume this id."""
    entry = _entries().get(session_id, {})
    return entry.get("backend")


def target_backend(session_id: str, default: str = DEFAULT_BACKEND) -> str:
    """The backend the NEXT turn runs on. A pending switch beats the lineage's own provider:
    a session cannot move between providers (AD-3), so choosing another backend is a promise
    about the next turn — which will be a new session — not an edit to this one."""
    pending = setting_for(session_id, "next_backend")
    owner = backend_for(session_id)
    return pending or owner or default


def switch_backend(session_id: str, name: str) -> None:
    """Arm (or cancel) a provider switch. Model and effort are cleared with it because they
    are provider-specific strings: `opus` means nothing to opencode and `openrouter/x/y`
    means nothing to claude, so carrying either across would build an argv the CLI rejects."""
    owner = backend_for(session_id)
    pending = None if name == owner else name
    set_setting(session_id, "next_backend", pending)
    set_setting(session_id, "model", None)
    set_setting(session_id, "effort", None)


def mode_for(session_id: str, default: str = DEFAULT_MODE) -> str:
    """Sticky per-session mode ∈ {build, plan}; defaults to build when unset."""
    return setting_for(session_id, "mode", default) or default


def set_mode(session_id: str, mode: str) -> None:
    set_setting(session_id, "mode", mode)


def title_for(session_id: str) -> str | None:
    entry = _entries().get(session_id, {})
    return entry.get("title")


def remember_context_window(model: str | None, window: int | None) -> None:
    """Learn a model's context window from a live turn. Claude transcripts don't record it, so
    the /resume list reuses what we've observed instead of hardcoding per-model constants."""
    if model and window:
        cfg = config.load_config()
        windows = cfg.get("context_windows", {})
        windows[model] = window
        config.save_config(context_windows=windows)


def context_window_for(model: str | None) -> int | None:
    """Observed context window for a model, or None if we've never seen a live turn on it."""
    windows = config.load_config().get("context_windows", {})
    return windows.get(model or "")


def _remember_by_message(map_name: str, message_id: int, value: str) -> None:
    """Bounded message_id -> value map (oldest ids evicted first). Shared by the
    reply-to-continue map and the pending-/new map."""
    cfg = config.load_config()
    mapping = cfg.get(map_name, {})
    mapping[str(message_id)] = value
    if len(mapping) > REPLY_MAP_MAX:
        stale = sorted(mapping, key=int)[: len(mapping) - REPLY_MAP_MAX]
        for key in stale:
            del mapping[key]
    config.save_config(**{map_name: mapping})


def _value_by_message(map_name: str, message_id: int) -> str | None:
    mapping = config.load_config().get(map_name, {})
    return mapping.get(str(message_id))


def remember_reply(message_id: int, session_id: str) -> None:
    """Anchor message -> session. Also what lets a panel tap resolve its session without
    spending any of callback_data's 64 bytes on an id (P2 D4)."""
    _remember_by_message("reply_map", message_id, session_id)


def session_for_reply(message_id: int) -> str | None:
    return _value_by_message("reply_map", message_id)


def remember_pending_new(message_id: int, backend: str) -> None:
    """A /new with no prompt asks for one via ForceReply; the answer to THAT message
    is the prompt, so remember which backend the pending session should use."""
    _remember_by_message("pending_new", message_id, backend)


def pending_new(message_id: int) -> str | None:
    return _value_by_message("pending_new", message_id)
