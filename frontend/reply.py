# reply.py — Telegram send primitives: safe reply, chunking, edit-in-place delivery.
from __future__ import annotations
from telegram.error import TelegramError

TELEGRAM_MSG_LIMIT = 4096


async def safe_reply(msg, html_text: str, reply_markup=None) -> "telegram.Message | None":
    result = None
    for attempt in range(2):
        try:
            result = await msg.reply_text(html_text, parse_mode="HTML", do_quote=True, reply_markup=reply_markup)
            break
        except TelegramError as e:
            if attempt == 1:
                print(f"reply_text failed after retry: {e}")
    return result


def _chunks(html_text: str, size: int) -> list[str]:
    parts = []
    for i in range(0, len(html_text), size):
        parts.append(html_text[i:i + size])
    if not parts:
        parts = [html_text]
    return parts


async def _edit_or_send(working_msg, msg, html_text: str) -> "telegram.Message | None":
    """Morph the ⏳ working message into the final text (feels like a substitution);
    fall back to a fresh reply if the edit is rejected (too old, identical, etc.)."""
    sent = None
    if working_msg is not None:
        try:
            sent = await working_msg.edit_text(html_text, parse_mode="HTML")
        except TelegramError as e:
            print(f"edit failed, sending instead: {e}")
    if sent is None:
        sent = await safe_reply(msg, html_text)
    return sent


async def deliver(working_msg, msg, html_text: str) -> "telegram.Message | None":
    chunks = _chunks(html_text, TELEGRAM_MSG_LIMIT)
    first = chunks[0]
    last = await _edit_or_send(working_msg, msg, first)
    for chunk in chunks[1:]:
        last = await safe_reply(msg, chunk)
    return last
