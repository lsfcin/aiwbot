# bot.py — PTB wiring: allowlist, /new + reply-to-continue dispatch, plain text/media -> INBOX.
from __future__ import annotations
from telegram import BotCommand, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from . import config, dispatch, format, inbox, msgmap, panel, panelmenu, phrases, registry, reply, resume, startword, stt, tts, turnhelpers

WORKSPACE_DIR = config.WORKSPACE_DIR
DEFAULT_BACKEND = registry.DEFAULT_BACKEND


_strip_bot_prefix = startword.strip_prefix


def _empty_guard(transcript: str) -> bool:
    """C3: an empty/whitespace-only transcript must not be dispatched."""
    return not transcript.strip()


async def _run_and_deliver(msg, working, prompt: str, *, session_id: str | None,
                           backend_name: str, title: str | None, scope: str,
                           spoken: bool = False) -> None:
    """Shared tail: dispatch one turn with the scope's sticky knobs, then deliver the answer
    with its footer + the anchor keyboard. `spoken` (C5) additionally replies with a voice
    note synthesized from the same answer — text-triggered turns leave it False and are
    unaffected."""
    options = turnhelpers.turn_options(scope, title)
    try:
        result = await dispatch.turn(prompt, session_id=session_id, backend_name=backend_name, cwd=WORKSPACE_DIR, options=options)
    except dispatch.DispatchError as e:
        await reply.deliver(working, msg, turnhelpers.friendly_error(e))
        return
    turnhelpers.persist_turn(result.session_id, backend_name, title, result, options)
    block = format.answer_block(result.text, result.session_id, title, provider=backend_name, model=result.model, cost_usd=result.cost_usd, mode=options.mode, context_used=result.context_used, context_window=result.context_window)
    markup = panelmenu.root_markup(result.session_id, options.mode)
    sent = await reply.deliver(working, msg, block, reply_markup=markup)
    if sent is not None:
        msgmap.remember_reply(sent.message_id, result.session_id)
    if spoken:
        try:
            speech_text = format.clip_chars(format.plain(result.text), 2000)
            ogg_bytes = tts.synthesize(speech_text)
            await reply.send_voice(msg, ogg_bytes)
        except Exception as e:
            print(f"voice reply failed: {e}")


async def _start_new(msg, prompt: str, *, spoken: bool = False) -> None:
    """A new session runs on the NEW scope: whatever the last interaction used, minus anything
    the /new config bubble changed since."""
    working = await reply.safe_reply(msg, format.plain(phrases.pick(phrases.WORKING_PHRASES)))
    title = format.title_from_prompt(prompt)
    harness = registry.harness_for(registry.NEW)
    await _run_and_deliver(msg, working, prompt, session_id=None, backend_name=harness,
                           title=title, scope=registry.NEW, spoken=spoken)


async def _cmd_new(msg, arg: str) -> None:
    """Tapping /new in Telegram's command menu sends it bare, so an empty prompt answers with a
    config bubble instead of an error: adjust harness/model/effort on it, then reply with the
    prompt. Telegram allows exactly one reply_markup per message, so this bubble carries the
    keyboard and gives up ForceReply's auto-focus — Lucas's call, 2026-07-23."""
    backend_name, prompt = turnhelpers.parse_new_arg(arg)
    if backend_name:
        registry.set_setting(registry.NEW, "backend", backend_name)
    if not prompt.strip():
        ask = format.plain(phrases.pick(phrases.NEW_EMPTY_PROMPT_PHRASES))
        current = registry.mode_for(registry.NEW)
        markup = panelmenu.root_markup(registry.NEW, current)
        asked = await reply.safe_reply(msg, ask, reply_markup=markup)
        if asked is not None:
            msgmap.remember_pending_new(asked.message_id)
        return
    await _start_new(msg, prompt)


async def _handle_reply_continue(msg, sid: str, text: str, *, spoken: bool = False) -> None:
    """`text` is the already-resolved prompt (msg.text for a text turn, the STT transcript for
    a voice turn) — read from the caller's arg, never re-derived from `msg.text`, since a voice
    message replying to a prior session anchor has no `.text` at all (only the transcript the
    caller already computed)."""
    harness = registry.backend_for(sid) or DEFAULT_BACKEND
    working = await reply.safe_reply(msg, format.plain(phrases.pick(phrases.WORKING_PHRASES)))
    title = registry.title_for(sid)
    await _run_and_deliver(msg, working, text, session_id=sid, backend_name=harness,
                           title=title, scope=sid, spoken=spoken)


async def _route_text(msg, text: str, context, *, spoken: bool = False) -> None:
    """Shared reply-continue / pending-new / "bot"-prefix / INBOX-fallback routing (steps
    3-6 of the old `_handle_message`), reused verbatim by text (spoken=False) and voice
    (spoken=True, C2/C5)."""
    if msg.reply_to_message is not None:
        replied_to = msg.reply_to_message.message_id
        sid = msgmap.session_for_reply(replied_to)
        if sid:
            await _handle_reply_continue(msg, sid, text, spoken=spoken)
            return
        awaiting = msgmap.pending_new(replied_to)
        if awaiting:
            await _start_new(msg, text, spoken=spoken)
            return
    bot_prompt = _strip_bot_prefix(text)
    if bot_prompt is not None:
        await _start_new(msg, bot_prompt, spoken=spoken)
        return
    inbox.append_entry(inbox.build_entry(text, None, forwarded=msg.forward_origin is not None))
    await reply.safe_reply(msg, format.plain(phrases.pick(phrases.CAPTURE_ACKS)))


async def _echo_transcript(msg, transcript: str) -> None:
    """F2: quote back what STT heard, as a reply to Lucas's own voice note and before the turn
    runs. Without it a mishearing is only ever inferred from a strange answer, minutes later —
    and it is the instrument the audio punctuation/cadence work tunes against."""
    quoted = format.plain(transcript)
    line = phrases.TRANSCRIPT_ECHO.format(text=quoted)
    await reply.safe_reply(msg, f"<blockquote>{line}</blockquote>")


async def _handle_voice(msg, context) -> None:
    """C1/C3: transcribe, then either route through the same text dispatch (spoken=True) or
    degrade safely to the untranscribed-INBOX fallback."""
    path = await inbox.save_media(msg.voice.file_id, context, ".ogg")
    transcript = stt.transcribe(path)
    if _empty_guard(transcript):
        inbox.append_entry(inbox.build_entry("voice note (untranscribed)", path, forwarded=msg.forward_origin is not None))
        await reply.safe_reply(msg, format.plain(phrases.pick(phrases.TRANSCRIBE_FAIL_PHRASES)))
        return
    await _echo_transcript(msg, transcript)
    await _route_text(msg, transcript, context, spoken=True)


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
    if msg.text:
        context.application.create_task(_route_text(msg, msg.text, context, spoken=False))
        return
    if msg.voice is not None:
        context.application.create_task(_handle_voice(msg, context))
        return
    forwarded = msg.forward_origin is not None
    if msg.photo:
        path = await inbox.save_media(msg.photo[-1].file_id, context, ".jpg")
        inbox.append_entry(inbox.build_entry(msg.caption or "(photo)", path, forwarded=forwarded))
    elif msg.document is not None:
        suffix = "." + (msg.document.file_name or "file").rsplit(".", 1)[-1]
        path = await inbox.save_media(msg.document.file_id, context, suffix)
        inbox.append_entry(inbox.build_entry(msg.caption or "(document)", path, forwarded=forwarded))
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
    app.add_handler(CallbackQueryHandler(panel.handle_callback, pattern="^p:"))
    app.add_handler(CallbackQueryHandler(resume.handle_callback, pattern="^(resume|page|noop):"))
    app.add_handler(MessageHandler(filters.ALL, _handle_message))
    print("aiwbot: polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
