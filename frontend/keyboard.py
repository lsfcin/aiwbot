# keyboard.py — the panel's fixed 5-column grid: two chrome columns framing three content cells.
from __future__ import annotations
from telegram import InlineKeyboardButton

# Telegram splits a row's width evenly between its buttons and has no colspan, so a cell is only
# square if every row holds the same number of them. Five columns is what makes ‹ › + x ··· −
# read as squares at phone width; the count is the whole geometry, so it lives here alone.
COLS = 5
CONTENT_COLS = 3
NOOP = "noop:"
# Braille blank: a label with no ink, so a filler cell renders as an empty button rather than a
# gap. Filler is not decoration — it is what keeps column N of one row above column N of the next.
BLANK = "⠀"


def blank() -> InlineKeyboardButton:
    return InlineKeyboardButton(BLANK, callback_data=NOOP)


def cell(label: str, data: str | None) -> InlineKeyboardButton:
    """A chrome cell. `data=None` means the slot exists for alignment but does nothing."""
    target = data or NOOP
    return InlineKeyboardButton(label, callback_data=target)


def segment(label: str, selected: bool) -> str:
    """Selected reads `[ BUILD ]`, the rest stay bare. Fixed positions mean only the bracket
    appears to move, which is what gives a plain button row a segmented-control feel (AD-5:
    labels are single-line, so the selection has to be spelled out inside the text)."""
    result = f"[ {label} ]" if selected else label
    return result


def chunk(buttons: list[InlineKeyboardButton], per_row: int) -> list[list[InlineKeyboardButton]]:
    rows = []
    for start in range(0, len(buttons), per_row):
        row = buttons[start:start + per_row]
        rows.append(row)
    return rows


def _slot(chrome: dict[int, InlineKeyboardButton], index: int) -> InlineKeyboardButton:
    found = chrome.get(index)
    result = found if found is not None else blank()
    return result


def grid(content: list[InlineKeyboardButton],
         left: dict[int, InlineKeyboardButton] | None = None,
         right: dict[int, InlineKeyboardButton] | None = None) -> list[list[InlineKeyboardButton]]:
    """Content wrapped three per row, each row framed by one chrome cell per side and padded to
    COLS. `left`/`right` are keyed by row index; every unclaimed slot becomes a blank, so the
    grid never changes shape and the columns stay aligned between rows."""
    rows = chunk(content, CONTENT_COLS)
    if not rows:
        rows = [[]]
    lefts = left or {}
    rights = right or {}
    built = []
    for index, row in enumerate(rows):
        framed = [_slot(lefts, index)]
        framed.extend(row)
        while len(framed) < COLS - 1:
            framed.append(blank())
        framed.append(_slot(rights, index))
        built.append(framed)
    return built
