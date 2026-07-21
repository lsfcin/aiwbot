# resume.py — /resume picker (Claude-Code-style): list recent sessions, tap to re-anchor + continue.
from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from . import config, format, phrases, reply, sessions

RESUME_COUNT = 8
LABEL_MAX = 60


def _label(item: dict) -> str:
    title = format.title_words(item["title"])
    when = format.relative_time(item["updated_at"])
    backend = item["backend"]
    label = f"{title} · {when} · {backend}"
    if len(label) > LABEL_MAX:
        label = label[:LABEL_MAX - 1] + "…"
    return label


def _keyboard(items: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        text = _label(item)
        data = f"resume:{item['session_id']}"
        button = InlineKeyboardButton(text, callback_data=data)
        rows.append([button])
    return InlineKeyboardMarkup(rows)


def _header(total: int, query: str) -> str:
    shown = min(total, RESUME_COUNT)
    base = f"Sessões recentes — {shown} de {total}"
    if query:
        base += f' · filtro "{query}"'
    return base


async def cmd_resume(msg, arg: str) -> None:
    query = arg.strip()
    items = sessions.recent(RESUME_COUNT, query)
    if not items:
        await reply.safe_reply(msg, format.plain(phrases.pick(phrases.RESUME_EMPTY_PHRASES)))
        return
    total = sessions.count(query)
    header = _header(total, query)
    keyboard = _keyboard(items)
    await reply.safe_reply(msg, format.plain(header), reply_markup=keyboard)


async def _anchor(query, sid: str) -> None:
    title = sessions.title_for(sid)
    phrase = phrases.pick(phrases.RESUME_ANCHOR_PHRASES)
    block = format.session_block(phrase, sid, title)
    sent = await reply.safe_reply(query.message, block)
    if sent is not None:
        sessions.remember_reply(sent.message_id, sid)


async def handle_callback(update, context) -> None:
    query = update.callback_query
    if query is None or query.message is None:
        return
    if query.message.chat_id != config.allowed_chat_id():
        return
    data = query.data or ""
    await query.answer()
    if data.startswith("resume:"):
        sid = data.split(":", 1)[1]
        await _anchor(query, sid)
