# panelmenu.py — the panel's states: mode row, dimension menu, value pickers with an expander.
from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from backend import backend_names, get_backend
from . import format, keyboard, registry

# Collapsed, the open control eats one of the four slots and the expander another, so two values
# fit; a picker with nothing to expand keeps that slot and shows three.
SLOTS = keyboard.MAX_PER_ROW - 2
# Expanded: three rows of four, minus the open control. The pager, when needed, is a fourth row.
PAGE = keyboard.MAX_PER_ROW * 3 - 1
_OPEN = "+"
_CLOSE = "x"
_MORE = "···"
_LESS = "−"
_PREV = "‹"
_NEXT = "›"
_ALL = "all"
# harness is absent from a live session on purpose: no CLI can import the other's transcript, so
# a running lineage can never change harness (SPECS AD-11). It exists only in the NEW scope.
_DIMS = {"h": "harness", "m": "model", "e": "effort"}
_SESSION_DIMS = ("m", "e")
_NEW_DIMS = ("h", "m", "e")


def _opener() -> InlineKeyboardButton:
    return keyboard.cell(_CLOSE, "p:root")


def _cells(values: list[str], current: str | None, dim: str) -> list[InlineKeyboardButton]:
    buttons = []
    for value in values:
        short = format.model_label(value) if dim == "m" else value
        label = keyboard.segment(short or value, value == current)
        button = InlineKeyboardButton(label, callback_data=f"p:s:{dim}:{value}")
        buttons.append(button)
    return buttons


def root_markup(scope: str, current_mode: str) -> InlineKeyboardMarkup:
    """What every answer and re-anchor carries: `+` to open the panel, then the mode segments.
    Nothing to expand here, so there is no trailing control."""
    modes = []
    for name in ("build", "plan"):
        selected = name == current_mode
        label = keyboard.segment(name.upper(), selected)
        button = InlineKeyboardButton(label, callback_data=f"p:mode:{name}")
        modes.append(button)
    opener = keyboard.cell(_OPEN, "p:menu")
    rows = keyboard.framed(opener, modes)
    return InlineKeyboardMarkup(rows)


def menu_markup(scope: str) -> InlineKeyboardMarkup:
    """`x` closes back to the mode row; the rest of the row is the dimensions."""
    keys = _NEW_DIMS if scope == registry.NEW else _SESSION_DIMS
    buttons = []
    for key in keys:
        button = InlineKeyboardButton(_DIMS[key], callback_data=f"p:d:{key}")
        buttons.append(button)
    rows = keyboard.framed(_opener(), buttons)
    return InlineKeyboardMarkup(rows)


def _pager(prefix: str, page: int, pages: int) -> list[InlineKeyboardButton]:
    """‹ N/M › as its own row, so the collapse control can stay the very last button."""
    back = f"{prefix}:{page - 1}" if page > 0 else None
    ahead = f"{prefix}:{page + 1}" if page + 1 < pages else None
    return [keyboard.cell(_PREV, back),
            keyboard.cell(f"{page + 1}/{pages}", None),
            keyboard.cell(_NEXT, ahead)]


def _paged(prefix: str, values: list[str], current: str | None, dim: str,
           page: int, extra: list) -> list[list]:
    pages = max(1, -(-len(values) // PAGE))
    start = page * PAGE
    shown = values[start:start + PAGE]
    buttons = _cells(shown, current, dim)
    if page + 1 == pages:
        buttons.extend(extra)
    tail = _pager(prefix, page, pages) if pages > 1 else None
    closer = keyboard.cell(_LESS, f"p:d:{dim}")
    return keyboard.framed(_opener(), buttons, closer, tail)


def _ordered(values: list[str], current: str | None) -> list[str]:
    """The collapsed row's candidates, selected-first whenever the selection would otherwise be
    at risk of falling off the cut — including when it came from the drill-down and is not in
    the shortlist at all. A picker that hides what is currently set is worse than one that
    reorders; while everything fits, natural order is kept and nothing moves."""
    if not current:
        ordered = values
    elif current not in values:
        ordered = [current] + values
    else:
        rest = [value for value in values if value != current]
        ordered = [current] + rest
    return ordered


def values_markup(dim: str, values: list[str], current: str | None, *,
                  expanded: bool = False, page: int = 0, extra: list = ()) -> InlineKeyboardMarkup:
    """One value picker. Collapsed is a single row: `x`, then two values and `···`, or three
    values when the list fits and there is nothing to expand. Expanded grows to three rows and
    pages past that, with `extra` (the model picker's `all`) on the last page."""
    candidates = _ordered(values, current)
    if expanded:
        rows = _paged(f"p:x:{dim}", candidates, current, dim, page, list(extra))
    else:
        deeper = len(candidates) > SLOTS + 1 or bool(extra)
        slots = SLOTS if deeper else SLOTS + 1
        shown = candidates[:slots]
        buttons = _cells(shown, current, dim)
        closer = keyboard.cell(_MORE, f"p:x:{dim}:0") if deeper else None
        rows = keyboard.framed(_opener(), buttons, closer)
    return InlineKeyboardMarkup(rows)


def _caps(scope: str):
    name = registry.harness_for(scope)
    backend = get_backend(name)
    return backend.capabilities()


def harness_values(scope: str) -> list[str]:
    return backend_names()


def model_values(scope: str) -> tuple[list[str], bool]:
    """(shortlist, whether a drill-down exists). claude's three aliases ARE its catalogue, so it
    gets no `all`; opencode's 478 across 6 providers always do."""
    caps = _caps(scope)
    sizes = [len(models) for models in caps.groups.values()]
    total = sum(sizes)
    deep = total > len(caps.favourites)
    return caps.favourites, deep


def effort_values(scope: str) -> list[str]:
    """Whatever the harness declares for the chosen model — empty when that model has no effort
    knob at all (opencode's toggle/budget_tokens shapes), which the caller reports rather than
    drawing a row of values --variant would refuse (SPECS AD-11)."""
    name = registry.harness_for(scope)
    backend = get_backend(name)
    model = registry.setting_for(scope, "model")
    return backend.efforts(model)


def all_button() -> InlineKeyboardButton:
    """Sits in the expanded model picker: the way out of the shortlist into every provider."""
    return InlineKeyboardButton(_ALL, callback_data="p:g")


def _provider_label(name: str) -> str:
    """Provider ids carry a qualifier nobody reads (`alibaba-coding-plan`, `ollama-cloud`), so
    only the leading word survives — already unique across the six configured here."""
    return name.split("-", 1)[0]


def providers_markup(scope: str) -> InlineKeyboardMarkup:
    """The drill-down's first level. `provider` here means who supplies the key (nvidia,
    openrouter) — the sense opencode uses. The harness is the CLI one level above it."""
    caps = _caps(scope)
    buttons = []
    for name in caps.groups:
        label = _provider_label(name)
        button = InlineKeyboardButton(label, callback_data=f"p:p:{name}:0")
        buttons.append(button)
    closer = keyboard.cell(_LESS, "p:d:m")
    rows = keyboard.framed(_opener(), buttons, closer)
    return InlineKeyboardMarkup(rows)


def provider_markup(scope: str, name: str, page: int) -> InlineKeyboardMarkup:
    """One page of a provider's models — openrouter alone holds 339, so this one always pages."""
    caps = _caps(scope)
    models = caps.groups.get(name) or []
    current = registry.setting_for(scope, "model")
    pages = max(1, -(-len(models) // PAGE))
    start = page * PAGE
    shown = models[start:start + PAGE]
    buttons = _cells(shown, current, "m")
    tail = _pager(f"p:p:{name}", page, pages) if pages > 1 else None
    closer = keyboard.cell(_LESS, "p:g")
    rows = keyboard.framed(_opener(), buttons, closer, tail)
    return InlineKeyboardMarkup(rows)
