# panelmenu.py — the panel's states drawn as keyboards: mode row, dimension menu, value pickers.
from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from . import choices, keyboard, labels, registry

# Collapsed, the back control eats one of the four slots and the expander another, so two values
# fit; a picker with nothing to expand keeps that slot and shows three.
SLOTS = keyboard.MAX_PER_ROW - 2
# Expanded: three rows of four, minus the back control. The pager, when needed, is a fourth row.
PAGE = keyboard.MAX_PER_ROW * 3 - 1
_OPEN = "+"
_BACK = "‹"
_MORE = "···"
_LESS = "−"
# Double angles for paging, single for going up a level: the back button and the previous-page
# button both sit in the leftmost slot of their row, so identical glyphs would stack vertically
# meaning two different things.
_PREV = "«"
_NEXT = "»"
_ALL = "all"


def _back(target: str) -> InlineKeyboardButton:
    """`‹` walks exactly one level up the menu tree. It used to be an `x` that jumped straight
    back to the mode row, which read as "cancel" rather than "back" — Lucas, 2026-07-23."""
    return keyboard.cell(_BACK, target)


def _cells(values: list[str], current: str | None, dim: str,
           qualify: bool = True) -> list[InlineKeyboardButton]:
    buttons = []
    for value in values:
        short = labels.model_label(value, qualify=qualify) if dim == "m" else value
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
    """`‹` goes back to the mode row; the rest of the row is whatever this scope can change."""
    buttons = []
    for key in choices.menu_dims(scope):
        button = InlineKeyboardButton(choices.LABELS[key], callback_data=f"p:d:{key}")
        buttons.append(button)
    rows = keyboard.framed(_back("p:root"), buttons)
    return InlineKeyboardMarkup(rows)


def _pager(prefix: str, page: int, pages: int) -> list[InlineKeyboardButton]:
    """« N/M » as its own row, so the collapse control can stay the very last button."""
    back = f"{prefix}:{page - 1}" if page > 0 else None
    ahead = f"{prefix}:{page + 1}" if page + 1 < pages else None
    return [keyboard.cell(_PREV, back),
            keyboard.cell(f"{page + 1}/{pages}", None),
            keyboard.cell(_NEXT, ahead)]


def _ordered(values: list[str], current: str | None, prefer: tuple = ()) -> list[str]:
    """The picker's candidates, selected-first whenever the selection would otherwise risk
    falling off the cut — including when it came from the drill-down and is not in the shortlist
    at all. A picker that hides what is currently set is worse than one that reorders. With
    nothing selected, `prefer` decides who gets the visible slots; the rest keep their order."""
    if current and current not in values:
        ordered = [current] + values
    elif current:
        rest = [value for value in values if value != current]
        ordered = [current] + rest
    elif prefer:
        head = [value for value in prefer if value in values]
        tail = [value for value in values if value not in head]
        ordered = head + tail
    else:
        ordered = values
    return ordered


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
    return keyboard.framed(_back("p:menu"), buttons, closer, tail)


def values_markup(dim: str, values: list[str], current: str | None, *,
                  expanded: bool = False, page: int = 0, extra: list = ()) -> InlineKeyboardMarkup:
    """One value picker. Collapsed is a single row: `‹`, then two values and `···`, or three
    values when the list fits and there is nothing to expand. Expanded grows to three rows and
    pages past that, with `extra` (the model picker's `all`) on the last page. Preference only
    reorders the collapsed slice — expanded keeps the declared order, which for effort is an
    ordinal ladder and should read as one."""
    if expanded:
        candidates = _ordered(values, current)
        rows = _paged(f"p:x:{dim}", candidates, current, dim, page, list(extra))
    else:
        prefer = choices.preferred(dim)
        candidates = _ordered(values, current, prefer)
        deeper = len(candidates) > SLOTS + 1 or bool(extra)
        slots = SLOTS if deeper else SLOTS + 1
        shown = candidates[:slots]
        buttons = _cells(shown, current, dim)
        closer = keyboard.cell(_MORE, f"p:x:{dim}:0") if deeper else None
        rows = keyboard.framed(_back("p:menu"), buttons, closer)
    return InlineKeyboardMarkup(rows)


def all_button() -> InlineKeyboardButton:
    """Sits in the expanded model picker: the way out of the shortlist into every provider."""
    return InlineKeyboardButton(_ALL, callback_data="p:g")


def _provider_label(name: str) -> str:
    """Provider ids carry a qualifier nobody reads (`alibaba-coding-plan`, `ollama-cloud`), so
    only the leading word survives — already unique across the six configured here."""
    return name.split("-", 1)[0]


def providers_markup(scope: str) -> InlineKeyboardMarkup:
    """The drill-down's first level: who supplies the key. Nothing to collapse, so no `−`."""
    buttons = []
    for name in choices.groups(scope):
        label = _provider_label(name)
        button = InlineKeyboardButton(label, callback_data=f"p:p:{name}:0")
        buttons.append(button)
    rows = keyboard.framed(_back("p:d:m"), buttons)
    return InlineKeyboardMarkup(rows)


def provider_markup(scope: str, name: str, page: int) -> InlineKeyboardMarkup:
    """One page of a provider's models — openrouter alone holds 339, so this one always pages."""
    models = choices.groups(scope).get(name) or []
    current = registry.setting_for(scope, "model")
    pages = max(1, -(-len(models) // PAGE))
    start = page * PAGE
    shown = models[start:start + PAGE]
    buttons = _cells(shown, current, "m", qualify=False)
    tail = _pager(f"p:p:{name}", page, pages) if pages > 1 else None
    rows = keyboard.framed(_back("p:g"), buttons, None, tail)
    return InlineKeyboardMarkup(rows)
