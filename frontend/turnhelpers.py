# turnhelpers.py — turn plumbing: friendly errors, /new arg parsing, sticky options, persistence.
# Extracted out of bot.py (size gate) — pure helpers with no test-visible monkeypatch seam.
from __future__ import annotations
from backend import TurnOptions
from . import directives, format, panel, phrases, registry

_BUSY_MARKERS = ("no conversation found", "currently running as a background agent")


def friendly_error(e: Exception) -> str:
    text = str(e).lower()
    busy = any(marker in text for marker in _BUSY_MARKERS)
    if busy:
        result = format.plain(phrases.pick(phrases.SESSION_LIVE_ELSEWHERE_PHRASES))
    else:
        result = format.plain(phrases.pick(phrases.ERROR_PHRASES, e=e))
    return result


def parse_new_arg(arg: str) -> tuple[str | None, str]:
    """`--backend X` still works and now simply writes the NEW scope's harness, so typing it
    and tapping it are the same act on the same state."""
    backend_name = None
    prompt = arg
    if arg.startswith("--backend "):
        rest = arg[len("--backend "):]
        parts = rest.split(maxsplit=1)
        backend_name = parts[0]
        prompt = parts[1] if len(parts) > 1 else ""
    return backend_name, prompt


def apply_directives(bot_prompt: str) -> str:
    """A `bot, …` message can name its own harness/model inline ("bot, opencode glm resume o
    pdf"); write those onto the NEW scope so the turn inherits them, and return the prompt with
    the directive words removed. Reuses `panel.apply` so an inline harness change clears a stale
    model exactly as a tapped one does — the invalidation rule stays in one place."""
    harness, model, rest = directives.resolve(bot_prompt)
    if harness:
        panel.apply(registry.NEW, "h", harness)
    if model:
        panel.apply(registry.NEW, "m", model)
    return rest


def turn_options(scope: str, title: str | None) -> TurnOptions:
    """The turn's knobs, read off the scope that owns them: a live session, or NEW for the
    last-used defaults a fresh session inherits."""
    mode_name = registry.mode_for(scope)
    model = registry.setting_for(scope, "model")
    effort = registry.setting_for(scope, "effort")
    return TurnOptions(mode=mode_name, title=title, model=model, effort=effort)


def persist_turn(session_id: str, backend_name: str, title: str | None, result, options: TurnOptions) -> None:
    """Carry the knobs onto the session the turn ran on, and onto the defaults, so the next
    /new starts where the last interaction left off."""
    preview = format.response_preview(result.text)
    registry.remember(session_id, backend_name, title, preview)
    registry.set_mode(session_id, options.mode)
    registry.set_setting(session_id, "model", options.model)
    registry.set_setting(session_id, "effort", options.effort)
    registry.remember_defaults(backend_name, options.mode, options.model, options.effort)
    registry.remember_context_window(result.model, result.context_window)
