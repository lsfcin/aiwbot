# mode.py — plan↔build segmented control: two footer buttons, selected one bracketed. Sticky/session.
from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from . import keyboard

MODES = ("build", "plan")


def toggle_row(session_id: str, mode: str) -> list[InlineKeyboardButton]:
    """One row, BUILD left / PLAN right (fixed). Each button carries its target mode + session
    id — the mode row predates the panel and its callback_data shape is kept so anchors already
    sitting in the chat keep working."""
    row = []
    for name in MODES:
        selected = name == mode
        label = name.upper()
        text = keyboard.segment(label, selected)
        data = f"mode:{name}:{session_id}"
        button = InlineKeyboardButton(text, callback_data=data)
        row.append(button)
    return row


def toggle_markup(session_id: str, mode: str) -> InlineKeyboardMarkup:
    """The mode row alone. `panel.root_markup` is what an anchor actually gets — this stays
    for callers that want the bare control (and for the tests that pin its shape)."""
    row = toggle_row(session_id, mode)
    return InlineKeyboardMarkup([row])
