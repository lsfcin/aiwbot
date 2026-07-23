# resume.py — /resume picker (Claude-Code-style): list recent sessions, tap to re-anchor + continue.
from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from . import config, format, phrases, reply, sessions

RESUME_COUNT = 5
TITLE_WORDS = 6


def _meta(item: dict) -> str:
    """L3: tempo · modo · provider · model — bits omitted when a session lacks them
    (VSCode sessions carry no bot mode/model beyond what the transcript records)."""
    when = format.relative_time(item["updated_at"])
    bits = [when]
    mode = item.get("mode")
    if mode:
        bits.append(mode)
    bits.append(item["backend"])
    model = format.short_model(item.get("model"))
    if model:
        bits.append(model)
    return " · ".join(bits)


def _entry_line(i: int, item: dict) -> str:
    """3 lines: `N. TÍTULO` / `<6 words> … <6 words>` of the last response / meta line."""
    title = format.title_words(item["title"], TITLE_WORDS)
    lines = [f"{i}. {title}"]
    preview = item.get("preview")
    if preview:
        rendered = format.response_preview(preview)
        lines.append(rendered)
    meta = _meta(item)
    lines.append(meta)
    return "\n".join(lines)


def _list_text(items: list[dict]) -> str:
    blocks = []
    for i, item in enumerate(items, start=1):
        block = _entry_line(i, item)
        blocks.append(block)
    return "\n\n".join(blocks)


def _keyboard(items: list[dict]) -> InlineKeyboardMarkup:
    row = []
    for i, item in enumerate(items, start=1):
        data = f"resume:{item['session_id']}"
        button = InlineKeyboardButton(str(i), callback_data=data)
        row.append(button)
    return InlineKeyboardMarkup([row])


def _header(total: int, shown: int, query: str) -> str:
    base = f"Sessões recentes — {shown} de {total}"
    if query:
        base += f' · filtro "{query}"'
    if total > shown:
        base += f" · /resume {total} pra ver todas"
    return base


def _parse_arg(arg: str) -> tuple[str, int]:
    query = arg
    count = RESUME_COUNT
    if arg.isdigit():
        query = ""
        count = int(arg)
    return query, count


async def cmd_resume(msg, arg: str, cwd: str) -> None:
    query, count = _parse_arg(arg.strip())
    items = sessions.recent(count, query, cwd)
    if not items:
        await reply.safe_reply(msg, format.plain(phrases.pick(phrases.RESUME_EMPTY_PHRASES)))
        return
    total = sessions.count(query, cwd)
    header = _header(total, len(items), query)
    text = f"{header}\n\n{_list_text(items)}"
    keyboard = _keyboard(items)
    await reply.safe_reply(msg, format.plain(text), reply_markup=keyboard)


async def _anchor(query, sid: str) -> None:
    title = sessions.title_for(sid)
    backend = sessions.backend_for(sid)
    phrase = phrases.pick(phrases.RESUME_ANCHOR_PHRASES)
    block = format.session_block(phrase, sid, title, backend=backend)
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
