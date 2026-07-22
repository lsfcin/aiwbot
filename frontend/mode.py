# mode.py — plan↔build toggle: inline button on the answer footer + its callback. Sticky per-session.
from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from . import config, sessions

_LABELS = {"build": "🧭 → plan", "plan": "🔨 → build"}
_FLIP = {"build": "plan", "plan": "build"}


def _label(mode: str) -> str:
    return _LABELS.get(mode, _LABELS["build"])


def toggle_markup(session_id: str, mode: str) -> InlineKeyboardMarkup:
    """One single-line button (AD-5) showing the flip target; taps carry the session id."""
    data = f"mode:{session_id}"
    button = InlineKeyboardButton(_label(mode), callback_data=data)
    return InlineKeyboardMarkup([[button]])


async def handle_callback(update, context) -> None:
    query = update.callback_query
    if query is None or query.message is None:
        return
    if query.message.chat_id != config.allowed_chat_id():
        return
    data = query.data or ""
    sid = data.split(":", 1)[1]
    current = sessions.mode_for(sid)
    new_mode = _FLIP.get(current, "plan")
    sessions.set_mode(sid, new_mode)
    await query.answer(f"modo: {new_mode}")
    markup = toggle_markup(sid, new_mode)
    await query.edit_message_reply_markup(reply_markup=markup)
