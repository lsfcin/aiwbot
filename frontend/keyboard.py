# keyboard.py — inline-keyboard primitives shared by every picker: segments, arrows, rows.
from __future__ import annotations
from telegram import InlineKeyboardButton

# An arrow parked at the end of a range keeps its slot so the row never changes shape; the tap
# is answered (spinner dismissed) and deliberately does nothing else.
NOOP = "noop:"


def segment(label: str, selected: bool) -> str:
    """Selected reads `[ BUILD ]`, the rest stay bare. Fixed positions mean only the bracket
    appears to move, which is what gives a plain button row a segmented-control feel (AD-5:
    labels are single-line, so the selection has to be spelled out inside the text)."""
    result = f"[ {label} ]" if selected else label
    return result


def arrow(glyph: str, data: str, live: bool) -> InlineKeyboardButton:
    """A page arrow: real callback_data while there is somewhere to go, `noop:` at the end."""
    target = data if live else NOOP
    return InlineKeyboardButton(glyph, callback_data=target)


def chunk(buttons: list[InlineKeyboardButton], per_row: int) -> list[list[InlineKeyboardButton]]:
    """Wrap a flat button list into rows. Long labels (model ids) truncate when too many share
    a row, so anything wordier than a mode name gets two per row instead of four."""
    rows = []
    for start in range(0, len(buttons), per_row):
        row = buttons[start:start + per_row]
        rows.append(row)
    return rows
