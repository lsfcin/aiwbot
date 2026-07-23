# resume.py — /resume picker (Claude-Code-style): list recent sessions, tap to re-anchor + continue.
from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from . import config, format, phrases, reply, sessions

RESUME_COUNT = 3
TITLE_WORDS = 5
ANCHOR_BODY_MAX = 3000
QUERY_MAX = 40  # callback_data caps at 64 bytes; the page arrows carry the active filter


def _meta(item: dict) -> str:
    """L3: provider · modelo · modo · X%contexto · quando — bits omitted when absent."""
    used = item.get("context_used")
    window = item.get("context_window")
    bits = format.meta_bits(item["backend"], item.get("model"), item.get("mode"), used, window)
    when = format.relative_time(item["updated_at"])
    bits.append(when)
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


def _list_text(items: list[dict], start: int = 1) -> str:
    blocks = []
    for i, item in enumerate(items, start=start):
        block = _entry_line(i, item)
        blocks.append(block)
    return "\n\n".join(blocks)


def _keyboard(items: list[dict], offset: int = 0, query: str = "", total: int = 0) -> InlineKeyboardMarkup:
    """One row: ‹ then the page's absolute numerals then ›. Numbering runs 1 2 3, 4 5 6, …
    so a numeral always names the same session as the line above it (AD-5)."""
    row = []
    if offset > 0:
        back = offset - RESUME_COUNT
        row.append(InlineKeyboardButton("‹", callback_data=f"page:{max(0, back)}:{query}"))
    for i, item in enumerate(items, start=offset + 1):
        data = f"resume:{item['session_id']}"
        row.append(InlineKeyboardButton(str(i), callback_data=data))
    shown = offset + len(items)
    if shown < total:
        row.append(InlineKeyboardButton("›", callback_data=f"page:{shown}:{query}"))
    return InlineKeyboardMarkup([row])


def _header(total: int, shown: int, query: str) -> str:
    base = f"Sessões recentes — {shown} de {total}"
    if query:
        base += f' · filtro "{query}"'
    return base


def _page(query: str, cwd: str, offset: int, count: int) -> tuple[str, InlineKeyboardMarkup] | None:
    """One page of the picker: message text + its ‹ N N N › keyboard. None when nothing matches."""
    items = sessions.recent(count, query, cwd, offset)
    result = None
    if items:
        total = sessions.count(query, cwd)
        header = _header(total, offset + len(items), query)
        listing = _list_text(items, offset + 1)
        text = f"{header}\n\n{listing}"
        keyboard = _keyboard(items, offset, query, total)
        result = (format.plain(text), keyboard)
    return result


def _parse_arg(arg: str) -> tuple[str, int]:
    query = arg
    count = RESUME_COUNT
    if arg.isdigit():
        query = ""
        count = int(arg)
    return query, count


async def cmd_resume(msg, arg: str, cwd: str) -> None:
    stripped = arg.strip()
    query, count = _parse_arg(stripped)
    page = _page(query[:QUERY_MAX], cwd, 0, count)
    if page is None:
        await reply.safe_reply(msg, format.plain(phrases.pick(phrases.RESUME_EMPTY_PHRASES)))
        return
    text, keyboard = page
    await reply.safe_reply(msg, text, reply_markup=keyboard)


async def _turn_page(query, data: str) -> None:
    """‹ / › tap: re-render the same message at the new offset (filter rides in callback_data)."""
    parts = data.split(":", 2)
    offset = int(parts[1])
    term = parts[2]
    page = _page(term, config.WORKSPACE_DIR, offset, RESUME_COUNT)
    if page is None:
        return
    text, keyboard = page
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)


def _clip(text: str, limit: int = ANCHOR_BODY_MAX) -> str:
    """Telegram caps a message at 4096; the anchor's last-response body is the only
    unbounded part, so clip the raw text before it gets formatted."""
    result = text
    if len(text) > limit:
        result = text[:limit] + "\n[…]"
    return result


async def _anchor(query, sid: str) -> None:
    title = sessions.title_for(sid)
    backend = sessions.backend_for(sid)
    answer = sessions.last_response(sid, config.WORKSPACE_DIR)
    body = _clip(answer) if answer else None
    phrase = phrases.pick(phrases.RESUME_ANCHOR_PHRASES)
    block = format.session_block(phrase, sid, title, body=body, backend=backend)
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
    elif data.startswith("page:"):
        await _turn_page(query, data)
