# mode.py — plan↔build segmented control: two footer buttons, selected one bracketed. Sticky/session.
from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from . import config, sessions

_MODES = ("build", "plan")


def _btn_label(mode: str, selected: bool) -> str:
    """Selected mode reads `[ BUILD ]`; the other stays bare. Fixed positions => only the
    bracket appears to move, giving a segmented-toggle feel (AD-5: single-line labels)."""
    label = mode.upper()
    result = f"[ {label} ]" if selected else label
    return result


def toggle_markup(session_id: str, mode: str) -> InlineKeyboardMarkup:
    """One row, BUILD left / PLAN right (fixed). Each button carries its target mode + session id."""
    row = []
    for m in _MODES:
        selected = m == mode
        text = _btn_label(m, selected)
        data = f"mode:{m}:{session_id}"
        button = InlineKeyboardButton(text, callback_data=data)
        row.append(button)
    return InlineKeyboardMarkup([row])


async def handle_callback(update, context) -> None:
    query = update.callback_query
    if query is None or query.message is None:
        return
    if query.message.chat_id != config.allowed_chat_id():
        return
    data = query.data or ""
    parts = data.split(":", 2)
    target = parts[1]
    sid = parts[2]
    await query.answer(f"modo: {target}")
    current = sessions.mode_for(sid)
    if target != current:
        markup = toggle_markup(sid, target)
        await query.edit_message_reply_markup(reply_markup=markup)
        sessions.set_mode(sid, target)
