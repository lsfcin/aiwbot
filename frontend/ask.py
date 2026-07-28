# ask.py — the bot side of ask_user: hold a running turn open on a question until Lucas answers.
# The agent's tool call blocks inside the daemon (askserver hands it here), so an answer resumes
# the SAME turn rather than starting a new one — that is the whole point of the MCP round trip.
from __future__ import annotations
import asyncio
import secrets
from dataclasses import dataclass, field
from telegram import InlineKeyboardMarkup
from . import format, keyboard, msgmap, phrases, reply

# Lucas asked for about an hour to answer, away from the PC (2026-07-27). The CLI's own ceiling
# on a tool call is raised past this in ClaudeBackend.env(), so this wait is the one that ends
# first and an unanswered question comes back as OUR text rather than as the CLI's timeout.
WAIT_SECONDS = 55 * 60
# Tap payload: `a:<question id>:<index>`. The option TEXT never travels in it — callback_data has
# 64 bytes and an option is written by the agent, so only the index rides along and the text is
# read back from the question the broker is still holding.
TAP = "a:"
# These three go to the AGENT, not to the chat: they are what the tool call returns when nobody
# answered. Text, never an MCP error — an error aborts the turn and throws away everything the
# agent had already worked out (Lucas's decision, 2026-07-27).
TIMEOUT_TEXT = ("sem resposta do usuário dentro do tempo de espera. siga com a hipótese mais "
                "razoável e diga explicitamente qual assumiu.")
ENDED_TEXT = "a conversa foi encerrada antes da resposta. siga sem ela."
EXPIRED_TEXT = "essa pergunta não pôde ser entregue ao usuário. siga sem ela."


@dataclass
class _Question:
    token: str
    future: asyncio.Future
    options: list[str] = field(default_factory=list)
    bubble: object | None = None


# token -> the message a question is sent as a reply to. One entry per LIVE turn: registered in
# turnrun before the backend is called and dropped in its `finally`, so a token can never outlive
# the turn that owns it.
_TURNS: dict[str, object] = {}
# question id -> the question still waiting for an answer.
_QUESTIONS: dict[str, _Question] = {}


def new_token() -> str:
    """Per-turn, unguessable, and short: it is spent in a URL the CLI is pointed at."""
    return secrets.token_hex(4)


def register(token: str, msg) -> None:
    _TURNS[token] = msg


def unregister(token: str) -> None:
    """End of the turn. Anything still waiting on this token is released here and now — a future
    nobody will ever resolve would leak a task per turn, and the tool call blocking on it would
    sit there until the CLI's own ceiling."""
    _TURNS.pop(token, None)
    stale = [qid for qid, item in _QUESTIONS.items() if item.token == token]
    for qid in stale:
        answer(qid, ENDED_TEXT)


def question_of(message_id: int) -> str | None:
    """Which unanswered question this message is asking, if any. Answered ones are dropped from
    the live map, so a reply to an old question bubble falls through to normal routing."""
    qid = msgmap.ask_question(message_id)
    live = qid if qid in _QUESTIONS else None
    return live


def answer(question_id: str, text: str) -> bool:
    """Resolve a waiting question. False when there is nothing to resolve — an evicted map entry,
    a question already answered, or a tap on a keyboard whose turn has ended."""
    item = _QUESTIONS.get(question_id)
    open_now = item is not None and not item.future.done()
    if open_now:
        item.future.set_result(text)
    return open_now


def answer_tap(data: str) -> bool:
    """A tapped button: `a:<question id>:<index>` back into the option text it stands for."""
    parts = data.split(":")
    resolved = False
    if len(parts) == 3:
        item = _QUESTIONS.get(parts[1])
        index = int(parts[2]) if parts[2].isdigit() else -1
        if item is not None and 0 <= index < len(item.options):
            resolved = answer(parts[1], item.options[index])
    return resolved


async def handle_callback(update, context) -> None:
    """PTB entry point for `a:` taps. The toast is the only feedback the tap itself gives — the
    real answer is the turn resuming and writing more text."""
    query = update.callback_query
    taken = answer_tap(query.data)
    note = phrases.ASK_TAKEN if taken else phrases.ASK_STALE
    await query.answer(text=note)


def _markup(question_id: str, options: list[str]):
    """Buttons only when the agent offered choices; a free-text reply always works as well."""
    markup = None
    if options:
        cells = [keyboard.cell(text, f"{TAP}{question_id}:{i}") for i, text in enumerate(options)]
        rows = keyboard.chunk(cells)
        markup = InlineKeyboardMarkup(rows)
    return markup


def _bubble_text(question: str, options: list[str]) -> str:
    """The question, then how to answer it. The hint is dropped when there are buttons: they say
    it themselves, and a hint under every question would read like boilerplate."""
    body = format.plain(question)
    line = f"▸ {body}"
    if not options:
        line = f"{line}\n\n{phrases.ASK_HINT}"
    return line


async def _close(item: _Question) -> None:
    """The question is settled: drop its keyboard so a later tap cannot pretend otherwise."""
    if item.bubble is not None and item.options:
        await reply.edit_text(item.bubble, item.bubble.text, None)


async def _wait(item: _Question) -> str:
    try:
        answered = await asyncio.wait_for(item.future, WAIT_SECONDS)
    except asyncio.TimeoutError:
        answered = TIMEOUT_TEXT
    return answered


async def _hold(origin, token: str, question: str, options: list[str]) -> str:
    qid = secrets.token_hex(3)
    loop = asyncio.get_running_loop()
    item = _Question(token=token, future=loop.create_future(), options=options)
    _QUESTIONS[qid] = item
    text = _bubble_text(question, options)
    item.bubble = await reply.safe_reply(origin, text, reply_markup=_markup(qid, options))
    answered = EXPIRED_TEXT
    if item.bubble is not None:
        msgmap.remember_ask(item.bubble.message_id, qid)
        answered = await _wait(item)
    _QUESTIONS.pop(qid, None)
    await _close(item)
    return answered


async def ask(token: str, question: str, options: list[str] | None = None) -> str:
    """Put the question in the chat and block the agent's tool call until it is answered.

    Every exit is a string, including the ones nobody answered: this return value goes straight
    back into the running turn, where an exception would end it instead."""
    origin = _TURNS.get(token)
    answered = EXPIRED_TEXT
    if origin is not None:
        answered = await _hold(origin, token, question, list(options or []))
    return answered
