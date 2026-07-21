# bot.py — PTB wiring: allowlist, /new + reply-to-continue dispatch, plain text/media -> INBOX.
from __future__ import annotations
from telegram import BotCommand, Update
from telegram.error import TelegramError
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from . import config, dispatch, format, inbox, phrases, sessions

WORKSPACE_DIR = "/mnt/workspace"
TELEGRAM_MSG_LIMIT = 4096
DEFAULT_BACKEND = "claude"
_BUSY_MARKERS = ("no conversation found", "currently running as a background agent")


def _friendly_error(e: Exception) -> str:
    text = str(e).lower()
    busy = any(marker in text for marker in _BUSY_MARKERS)
    if busy:
        result = format.plain(phrases.pick(phrases.SESSION_LIVE_ELSEWHERE_PHRASES))
    else:
        result = format.plain(phrases.pick(phrases.ERROR_PHRASES, e=e))
    return result


async def _safe_reply(msg, html_text: str) -> "telegram.Message | None":
    result = None
    for attempt in range(2):
        try:
            result = await msg.reply_text(html_text, parse_mode="HTML", do_quote=True)
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
        sent = await _safe_reply(msg, html_text)
    return sent


async def _deliver(working_msg, msg, html_text: str) -> "telegram.Message | None":
    chunks = _chunks(html_text, TELEGRAM_MSG_LIMIT)
    first = chunks[0]
    last = await _edit_or_send(working_msg, msg, first)
    for chunk in chunks[1:]:
        last = await _safe_reply(msg, chunk)
    return last


def _parse_new_arg(arg: str) -> tuple[str, str]:
    backend_name = DEFAULT_BACKEND
    prompt = arg
    if arg.startswith("--backend "):
        rest = arg[len("--backend "):]
        parts = rest.split(maxsplit=1)
        backend_name = parts[0]
        prompt = parts[1] if len(parts) > 1 else ""
    return backend_name, prompt


async def _cmd_new(msg, arg: str) -> None:
    backend_name, prompt = _parse_new_arg(arg)
    if not prompt.strip():
        await _safe_reply(msg, format.plain(phrases.pick(phrases.NEW_EMPTY_PROMPT_PHRASES)))
        return
    working = await _safe_reply(msg, format.plain(phrases.pick(phrases.WORKING_PHRASES)))
    try:
        result = await dispatch.turn(prompt, session_id=None, backend_name=backend_name, cwd=WORKSPACE_DIR)
    except dispatch.DispatchError as e:
        await _deliver(working, msg, _friendly_error(e))
        return
    sessions.remember(result.session_id, backend_name)
    block = format.session_block(phrases.pick(phrases.NEW_STARTED_PHRASES), result.session_id, None, body=result.text)
    sent = await _deliver(working, msg, block)
    if sent is not None:
        sessions.remember_reply(sent.message_id, result.session_id)


async def _handle_reply_continue(msg, sid: str) -> None:
    backend_name = sessions.backend_for(sid) or DEFAULT_BACKEND
    working = await _safe_reply(msg, format.plain(phrases.pick(phrases.WORKING_PHRASES)))
    try:
        result = await dispatch.turn(msg.text, session_id=sid, backend_name=backend_name, cwd=WORKSPACE_DIR)
    except dispatch.DispatchError as e:
        await _deliver(working, msg, _friendly_error(e))
        return
    sessions.remember(result.session_id, backend_name)
    extra = f"${result.cost_usd:.3f}" if result.cost_usd else None
    block = format.session_block(phrases.pick(phrases.CONTINUE_REPLY_PHRASES), result.session_id, None, body=result.text, extra=extra)
    sent = await _deliver(working, msg, block)
    if sent is not None:
        sessions.remember_reply(sent.message_id, result.session_id)


async def _dispatch_command(text: str, msg) -> None:
    parts = text.split(maxsplit=1)
    cmd, arg = parts[0], (parts[1].strip() if len(parts) > 1 else "")
    if cmd == "/help":
        await _safe_reply(msg, phrases.HELP_TEXT)
    elif cmd == "/new":
        await _cmd_new(msg, arg)
    else:
        await _safe_reply(msg, format.plain(phrases.pick(phrases.UNKNOWN_CMD_PHRASES, cmd=cmd)))


async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.chat_id != config.allowed_chat_id():
        return
    msg = update.message
    if msg.text and msg.text.startswith("/"):
        context.application.create_task(_dispatch_command(msg.text, msg))
        return
    if msg.text and msg.reply_to_message is not None:
        sid = sessions.session_for_reply(msg.reply_to_message.message_id)
        if sid:
            context.application.create_task(_handle_reply_continue(msg, sid))
            return
    if msg.voice is not None:
        path = await inbox.save_media(msg.voice.file_id, context, ".ogg")
        inbox.append_entry(inbox.build_entry("voice note (untranscribed)", path))
    elif msg.photo:
        path = await inbox.save_media(msg.photo[-1].file_id, context, ".jpg")
        inbox.append_entry(inbox.build_entry(msg.caption or "(photo)", path))
    elif msg.document is not None:
        suffix = "." + (msg.document.file_name or "file").rsplit(".", 1)[-1]
        path = await inbox.save_media(msg.document.file_id, context, suffix)
        inbox.append_entry(inbox.build_entry(msg.caption or "(document)", path))
    elif msg.text:
        inbox.append_entry(inbox.build_entry(msg.text, None))
    else:
        return
    await _safe_reply(msg, format.plain(phrases.pick(phrases.CAPTURE_ACKS)))


async def _post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("new", "Inicia sessão nova com um prompt"),
        BotCommand("help", "Lista os comandos"),
    ])


def main() -> None:
    app = Application.builder().token(config.bot_token()).post_init(_post_init).build()
    app.add_handler(MessageHandler(filters.ALL, _handle_message))
    print("aiwbot: polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
