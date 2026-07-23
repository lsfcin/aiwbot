# bot.py — PTB wiring: allowlist, /new + reply-to-continue dispatch, plain text/media -> INBOX.
from __future__ import annotations
from telegram import BotCommand, ForceReply, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from backend import TurnOptions
from . import config, dispatch, format, inbox, panel, phrases, registry, reply, resume

WORKSPACE_DIR = config.WORKSPACE_DIR
DEFAULT_BACKEND = registry.DEFAULT_BACKEND
_BUSY_MARKERS = ("no conversation found", "currently running as a background agent")


def _friendly_error(e: Exception) -> str:
    text = str(e).lower()
    busy = any(marker in text for marker in _BUSY_MARKERS)
    if busy:
        result = format.plain(phrases.pick(phrases.SESSION_LIVE_ELSEWHERE_PHRASES))
    else:
        result = format.plain(phrases.pick(phrases.ERROR_PHRASES, e=e))
    return result


def _strip_bot_prefix(text: str) -> str | None:
    lowered = text.lower()
    has_prefix = lowered.startswith("bot ") or lowered.startswith("bot,")
    prompt = text[4:].strip() if has_prefix else None
    return prompt


def _parse_new_arg(arg: str) -> tuple[str, str]:
    backend_name = DEFAULT_BACKEND
    prompt = arg
    if arg.startswith("--backend "):
        rest = arg[len("--backend "):]
        parts = rest.split(maxsplit=1)
        backend_name = parts[0]
        prompt = parts[1] if len(parts) > 1 else ""
    return backend_name, prompt


def _options(knobs_from: str | None, title: str | None) -> TurnOptions:
    """The turn's knobs, read off the session whose panel set them. A new session started by a
    backend switch reads them from the OLD session — which is why switch_backend clears the
    provider-specific ones first (registry.switch_backend)."""
    if knobs_from is None:
        return TurnOptions(title=title)
    mode_name = registry.mode_for(knobs_from)
    model = registry.setting_for(knobs_from, "model")
    effort = registry.setting_for(knobs_from, "effort")
    return TurnOptions(mode=mode_name, title=title, model=model, effort=effort)


def _persist(session_id: str, backend_name: str, title: str | None, result, options: TurnOptions) -> None:
    """Carry the knobs onto whatever session id the turn ended up on — the same one on a
    resume, a brand-new one after a backend switch."""
    preview = format.response_preview(result.text)
    registry.remember(session_id, backend_name, title, preview)
    registry.set_mode(session_id, options.mode)
    registry.set_setting(session_id, "model", options.model)
    registry.set_setting(session_id, "effort", options.effort)
    registry.remember_context_window(result.model, result.context_window)


async def _run_and_deliver(msg, working, prompt: str, *, session_id: str | None,
                           backend_name: str, title: str | None, knobs_from: str | None = None) -> None:
    """Shared tail: dispatch one turn with the session's sticky knobs, then deliver the answer
    with its footer + the anchor keyboard. New sessions default to build, no model, no effort."""
    source = knobs_from if knobs_from is not None else session_id
    options = _options(source, title)
    try:
        result = await dispatch.turn(prompt, session_id=session_id, backend_name=backend_name, cwd=WORKSPACE_DIR, options=options)
    except dispatch.DispatchError as e:
        await reply.deliver(working, msg, _friendly_error(e))
        return
    _persist(result.session_id, backend_name, title, result, options)
    block = format.answer_block(result.text, result.session_id, title, provider=backend_name, model=result.model, cost_usd=result.cost_usd, mode=options.mode, context_used=result.context_used, context_window=result.context_window)
    markup = panel.root_markup(result.session_id, options.mode)
    sent = await reply.deliver(working, msg, block, reply_markup=markup)
    if sent is not None:
        registry.remember_reply(sent.message_id, result.session_id)


async def _start_new(msg, backend_name: str, prompt: str) -> None:
    working = await reply.safe_reply(msg, format.plain(phrases.pick(phrases.WORKING_PHRASES)))
    title = format.title_from_prompt(prompt)
    await _run_and_deliver(msg, working, prompt, session_id=None, backend_name=backend_name, title=title)


async def _cmd_new(msg, arg: str) -> None:
    """Tapping /new in Telegram's command menu sends it bare — so instead of erroring,
    ask for the prompt with a ForceReply and start the session from that answer."""
    backend_name, prompt = _parse_new_arg(arg)
    if not prompt.strip():
        ask = format.plain(phrases.pick(phrases.NEW_EMPTY_PROMPT_PHRASES))
        force = ForceReply(input_field_placeholder="prompt da nova sessão")
        asked = await reply.safe_reply(msg, ask, reply_markup=force)
        if asked is not None:
            registry.remember_pending_new(asked.message_id, backend_name)
        return
    await _start_new(msg, backend_name, prompt)


async def _handle_reply_continue(msg, sid: str) -> None:
    """A pending backend switch can't resume this lineage (AD-3), so it opens a new session on
    the chosen provider instead, carrying the title and the mode over."""
    owner = registry.backend_for(sid) or DEFAULT_BACKEND
    target = registry.target_backend(sid, DEFAULT_BACKEND)
    switching = target != owner
    working = await reply.safe_reply(msg, format.plain(phrases.pick(phrases.WORKING_PHRASES)))
    title = registry.title_for(sid)
    resumed = None if switching else sid
    if switching:
        registry.set_setting(sid, "next_backend", None)
    await _run_and_deliver(msg, working, msg.text, session_id=resumed, backend_name=target,
                           title=title, knobs_from=sid)


async def _dispatch_command(text: str, msg) -> None:
    parts = text.split(maxsplit=1)
    cmd, arg = parts[0], (parts[1].strip() if len(parts) > 1 else "")
    if cmd == "/help":
        await reply.safe_reply(msg, phrases.HELP_TEXT)
    elif cmd == "/new":
        await _cmd_new(msg, arg)
    elif cmd == "/resume":
        await resume.cmd_resume(msg, arg, WORKSPACE_DIR)
    else:
        await reply.safe_reply(msg, format.plain(phrases.pick(phrases.UNKNOWN_CMD_PHRASES, cmd=cmd)))


async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.chat_id != config.allowed_chat_id():
        return
    msg = update.message
    if msg.text and msg.text.startswith("/"):
        context.application.create_task(_dispatch_command(msg.text, msg))
        return
    if msg.text and msg.reply_to_message is not None:
        replied_to = msg.reply_to_message.message_id
        sid = registry.session_for_reply(replied_to)
        if sid:
            context.application.create_task(_handle_reply_continue(msg, sid))
            return
        awaiting = registry.pending_new(replied_to)
        if awaiting:
            context.application.create_task(_start_new(msg, awaiting, msg.text))
            return
    if msg.text:
        bot_prompt = _strip_bot_prefix(msg.text)
        if bot_prompt is not None:
            context.application.create_task(_cmd_new(msg, bot_prompt))
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
    await reply.safe_reply(msg, format.plain(phrases.pick(phrases.CAPTURE_ACKS)))


async def _post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("new", "Inicia sessão nova com um prompt"),
        BotCommand("resume", "Retoma uma sessão recente"),
        BotCommand("help", "Lista os comandos"),
    ])


def main() -> None:
    app = Application.builder().token(config.bot_token()).post_init(_post_init).build()
    app.add_handler(CallbackQueryHandler(panel.handle_callback, pattern="^(mode|p):"))
    app.add_handler(CallbackQueryHandler(resume.handle_callback, pattern="^(resume|page|noop):"))
    app.add_handler(MessageHandler(filters.ALL, _handle_message))
    print("aiwbot: polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
