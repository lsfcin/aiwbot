# panelmenu.py — the settings panel's keyboard states: provedor / modelo / esforço, and the drill-down.
from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from backend import backend_names, get_backend
from . import format, keyboard, registry

PER_PAGE = 6
GEAR = "⚙"
_DIMS = (("b", "provedor"), ("m", "modelo"), ("e", "esforço"))
_BACK = "‹"
_FORWARD = "›"
_MORE = "mais…"
_CLOSE = "✕"
_AJUSTES = "ajustes"


def _framed(rows: list[list[InlineKeyboardButton]], back: str, where: str) -> InlineKeyboardMarkup:
    """Every state keeps a back button in its own row, so no state is a dead end. It NAMES its
    destination: the paged model list already owns a `‹` for the previous page, and two bare
    arrows meaning different things in one keyboard is exactly how a picker gets confusing."""
    label = f"{_BACK} {where}"
    button = InlineKeyboardButton(label, callback_data=back)
    framed = list(rows)
    framed.append([button])
    return InlineKeyboardMarkup(framed)


def summary(session_id: str) -> str:
    """Gear label: what the next turn will actually run on, unset knobs simply absent."""
    bits = [registry.target_backend(session_id)]
    model = registry.setting_for(session_id, "model")
    if model:
        short = format.short_model(model)
        bits.append(short)
    effort = registry.setting_for(session_id, "effort")
    if effort:
        bits.append(effort)
    joined = " · ".join(bits)
    return f"{GEAR} {joined}"


def menu_markup() -> InlineKeyboardMarkup:
    row = []
    for dim, label in _DIMS:
        button = InlineKeyboardButton(label, callback_data=f"p:d:{dim}")
        row.append(button)
    close = InlineKeyboardButton(_CLOSE, callback_data="p:root")
    row.append(close)
    return InlineKeyboardMarkup([row])


def _value_buttons(dim: str, values: list[str], current: str | None) -> list[InlineKeyboardButton]:
    buttons = []
    for value in values:
        short = format.model_label(value) if dim == "m" else value
        label = keyboard.segment(short or value, value == current)
        button = InlineKeyboardButton(label, callback_data=f"p:s:{dim}:{value}")
        buttons.append(button)
    return buttons


def _caps(session_id: str):
    name = registry.target_backend(session_id)
    backend = get_backend(name)
    return backend.capabilities()


def backend_markup(session_id: str) -> InlineKeyboardMarkup:
    names = backend_names()
    current = registry.target_backend(session_id)
    buttons = _value_buttons("b", names, current)
    rows = keyboard.chunk(buttons, 2)
    return _framed(rows, "p:menu", _AJUSTES)


def model_markup(session_id: str) -> InlineKeyboardMarkup:
    """Favourites first — the one-tap case P2 exists for. `mais…` appears only when the
    catalogue is actually bigger than the shortlist: claude's three aliases ARE its catalogue,
    so it never shows there, while opencode's 478 always do."""
    caps = _caps(session_id)
    current = registry.setting_for(session_id, "model")
    buttons = _value_buttons("m", caps.favourites, current)
    rows = keyboard.chunk(buttons, 2)
    sizes = [len(models) for models in caps.groups.values()]
    total = sum(sizes)
    if total > len(caps.favourites):
        more = InlineKeyboardButton(_MORE, callback_data="p:g")
        rows.append([more])
    return _framed(rows, "p:menu", _AJUSTES)


def group_markup(session_id: str) -> InlineKeyboardMarkup:
    """Level one of the drill-down: providers, each with its model count."""
    caps = _caps(session_id)
    buttons = []
    for name, models in caps.groups.items():
        label = f"{name} ({len(models)})"
        button = InlineKeyboardButton(label, callback_data=f"p:g:{name}:0")
        buttons.append(button)
    rows = keyboard.chunk(buttons, 2)
    return _framed(rows, "p:d:m", "modelo")


def _pager(name: str, offset: int, shown: int, total: int) -> list[InlineKeyboardButton]:
    back = offset - PER_PAGE
    if back < 0:
        back = 0
    ahead = offset + PER_PAGE
    left = keyboard.arrow(_BACK, f"p:g:{name}:{back}", offset > 0)
    counter = InlineKeyboardButton(f"{shown} / {total}", callback_data=keyboard.NOOP)
    right = keyboard.arrow(_FORWARD, f"p:g:{name}:{ahead}", ahead < total)
    return [left, counter, right]


def group_page_markup(session_id: str, name: str, offset: int) -> InlineKeyboardMarkup:
    """Level two: one page of a provider's models. openrouter alone carries 339, so the
    counter says where you are instead of pretending the list is short."""
    caps = _caps(session_id)
    models = caps.groups.get(name) or []
    page = models[offset:offset + PER_PAGE]
    current = registry.setting_for(session_id, "model")
    buttons = _value_buttons("m", page, current)
    rows = keyboard.chunk(buttons, 2)
    shown = offset + len(page)
    pager = _pager(name, offset, shown, len(models))
    rows.append(pager)
    return _framed(rows, "p:g", "provedores")


def efforts_for(session_id: str) -> list[str]:
    """Whatever the target backend declares for the chosen model — empty when that model has
    no effort knob at all (opencode's toggle/budget_tokens shapes), which the caller reports
    rather than drawing an empty row (SPECS AD-11)."""
    name = registry.target_backend(session_id)
    backend = get_backend(name)
    model = registry.setting_for(session_id, "model")
    return backend.efforts(model)


def effort_markup(session_id: str, values: list[str]) -> InlineKeyboardMarkup:
    current = registry.setting_for(session_id, "effort")
    buttons = _value_buttons("e", values, current)
    rows = keyboard.chunk(buttons, 3)
    return _framed(rows, "p:menu", _AJUSTES)
