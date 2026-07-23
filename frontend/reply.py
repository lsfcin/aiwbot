# reply.py — Telegram send primitives: safe reply, chunking, edit-in-place delivery.
from __future__ import annotations
from telegram.error import TelegramError
from .htmlsplit import split_html, strip_tags

TELEGRAM_MSG_LIMIT = 4096
# Telegram's wording when it rejects our markup rather than the request itself. Retrying the
# same HTML after one of these is pointless — the content is what it objects to.
_PARSE_MARKERS = ("parse entities", "start tag", "end tag", "entity")


def _is_parse_error(e: TelegramError) -> bool:
    text = str(e).lower()
    result = False
    for marker in _PARSE_MARKERS:
        if marker in text:
            result = True
            break
    return result


async def _send(msg, text: str, markup, parse_mode: str | None) -> "telegram.Message | None":
    return await msg.reply_text(text, parse_mode=parse_mode, do_quote=True, reply_markup=markup)


async def _send_plain(msg, html_text: str, reply_markup) -> "telegram.Message | None":
    """Telegram refused our markup: send the same content with the tags stripped. A message
    that lost its formatting still beats a message that silently never arrives."""
    bare = strip_tags(html_text)
    result = None
    try:
        result = await _send(msg, bare, reply_markup, None)
    except TelegramError as e:
        print(f"plain-text fallback failed too: {e}")
    return result


async def safe_reply(msg, html_text: str, reply_markup=None) -> "telegram.Message | None":
    result = None
    for attempt in range(2):
        try:
            result = await _send(msg, html_text, reply_markup, "HTML")
            break
        except TelegramError as e:
            if _is_parse_error(e):
                result = await _send_plain(msg, html_text, reply_markup)
                break
            if attempt == 1:
                print(f"reply_text failed after retry: {e}")
    return result


async def _edit_or_send(working_msg, msg, html_text: str, reply_markup=None) -> "telegram.Message | None":
    """Morph the ⏳ working message into the final text (feels like a substitution);
    fall back to a fresh reply if the edit is rejected (too old, identical, unparseable)."""
    sent = None
    if working_msg is not None:
        try:
            sent = await working_msg.edit_text(html_text, parse_mode="HTML", reply_markup=reply_markup)
        except TelegramError as e:
            print(f"edit failed, sending instead: {e}")
    if sent is None:
        sent = await safe_reply(msg, html_text, reply_markup=reply_markup)
    return sent


async def deliver(working_msg, msg, html_text: str, reply_markup=None) -> "telegram.Message | None":
    chunks = split_html(html_text, TELEGRAM_MSG_LIMIT)
    first = chunks[0]
    single = len(chunks) == 1
    markup = reply_markup if single else None
    last = await _edit_or_send(working_msg, msg, first, markup)
    for i, chunk in enumerate(chunks[1:]):
        is_last = i == len(chunks) - 2
        tail_markup = reply_markup if is_last else None
        last = await safe_reply(msg, chunk, reply_markup=tail_markup)
    return last
