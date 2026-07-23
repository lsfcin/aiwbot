# panelmenu.py — the panel's states as 5-column grids: mode row, dimension menu, value pickers.
from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from backend import backend_names, get_backend
from . import format, keyboard, registry

# One expanded screen: three rows of three. Collapsed shows the first row only.
PAGE = keyboard.CONTENT_COLS * 3
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


def _cells(values: list[str], current: str | None, dim: str) -> list[InlineKeyboardButton]:
    buttons = []
    for value in values:
        short = format.model_label(value) if dim == "m" else value
        label = keyboard.segment(short or value, value == current)
        button = InlineKeyboardButton(label, callback_data=f"p:s:{dim}:{value}")
        buttons.append(button)
    return buttons


def root_markup(scope: str, current_mode: str) -> InlineKeyboardMarkup:
    """What every answer and re-anchor carries: mode, plus one square `+` opening the panel.
    The `+` sits in the left chrome column, so it is the same width as every other cell."""
    modes = []
    for name in ("build", "plan"):
        selected = name == current_mode
        label = keyboard.segment(name.upper(), selected)
        button = InlineKeyboardButton(label, callback_data=f"p:mode:{name}")
        modes.append(button)
    opener = keyboard.cell(_OPEN, "p:menu")
    rows = keyboard.grid(modes, left={0: opener})
    return InlineKeyboardMarkup(rows)


def menu_markup(scope: str) -> InlineKeyboardMarkup:
    """`x` closes back to the mode row; the three content cells are the dimensions."""
    keys = _NEW_DIMS if scope == registry.NEW else _SESSION_DIMS
    buttons = []
    for key in keys:
        button = InlineKeyboardButton(_DIMS[key], callback_data=f"p:d:{key}")
        buttons.append(button)
    closer = keyboard.cell(_CLOSE, "p:root")
    rows = keyboard.grid(buttons, left={0: closer})
    return InlineKeyboardMarkup(rows)


def _pager(prefix: str, page: int, pages: int) -> tuple[dict, dict]:
    """‹ › live in the chrome columns of the last row, which is what makes them square, with
    the page counter filling the otherwise dead middle-left cell."""
    left: dict[int, InlineKeyboardButton] = {}
    right: dict[int, InlineKeyboardButton] = {}
    if pages > 1:
        left[1] = keyboard.cell(f"{page + 1}/{pages}", None)
        left[2] = keyboard.cell(_PREV, f"{prefix}:{page - 1}" if page > 0 else None)
        right[2] = keyboard.cell(_NEXT, f"{prefix}:{page + 1}" if page + 1 < pages else None)
    return left, right


def values_markup(dim: str, values: list[str], current: str | None, *,
                  expanded: bool = False, page: int = 0, extra: list = ()) -> InlineKeyboardMarkup:
    """One value picker. Collapsed is exactly one row of three, whatever the list length —
    everything past that lives behind `···`. Expanded is the same grid grown to three rows,
    paged past nine, with `extra` (the model picker's `all`) parked on the last page."""
    if not expanded:
        shown = values[:keyboard.CONTENT_COLS]
        buttons = _cells(shown, current, dim)
        deeper = len(values) > keyboard.CONTENT_COLS or bool(extra)
        opener = keyboard.cell(_MORE, f"p:x:{dim}:0") if deeper else None
        right = {0: opener} if opener else {}
        rows = keyboard.grid(buttons, left={0: keyboard.cell(_CLOSE, "p:root")}, right=right)
        return InlineKeyboardMarkup(rows)
    pages = max(1, -(-len(values) // PAGE))
    start = page * PAGE
    shown = values[start:start + PAGE]
    buttons = _cells(shown, current, dim)
    if page + 1 == pages:
        buttons.extend(extra)
    left, right = _pager(f"p:x:{dim}", page, pages)
    left[0] = keyboard.cell(_CLOSE, "p:root")
    right[0] = keyboard.cell(_LESS, f"p:d:{dim}")
    rows = keyboard.grid(buttons, left=left, right=right)
    return InlineKeyboardMarkup(rows)


def _caps(scope: str):
    name = registry.harness_for(scope)
    backend = get_backend(name)
    return backend.capabilities()


def harness_values(scope: str) -> list[str]:
    return backend_names()


def model_values(scope: str) -> tuple[list[str], bool]:
    """(shortlist, whether a drill-down exists). claude's three aliases ARE its catalogue, so
    it gets no `all`; opencode's 478 across 6 providers always do."""
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
    """Sits in the expanded model grid: the way out of the shortlist into every provider."""
    return InlineKeyboardButton(_ALL, callback_data="p:g")


def _provider_label(name: str) -> str:
    """A cell is a fifth of the bubble, so a label past ~9 characters is truncated by the
    client. Provider ids carry a qualifier nobody reads (`alibaba-coding-plan`,
    `ollama-cloud`), so only the leading word survives — it is already unique across the six."""
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
    left = {0: keyboard.cell(_CLOSE, "p:root")}
    right = {0: keyboard.cell(_LESS, "p:d:m")}
    rows = keyboard.grid(buttons, left=left, right=right)
    return InlineKeyboardMarkup(rows)


def provider_markup(scope: str, name: str, page: int) -> InlineKeyboardMarkup:
    """One page of a provider's models, same 3×3 grid — openrouter alone holds 339."""
    caps = _caps(scope)
    models = caps.groups.get(name) or []
    pages = max(1, -(-len(models) // PAGE))
    start = page * PAGE
    shown = models[start:start + PAGE]
    current = registry.setting_for(scope, "model")
    buttons = _cells(shown, current, "m")
    left, right = _pager(f"p:p:{name}", page, pages)
    left[0] = keyboard.cell(_CLOSE, "p:root")
    right[0] = keyboard.cell(_LESS, "p:g")
    rows = keyboard.grid(buttons, left=left, right=right)
    return InlineKeyboardMarkup(rows)
