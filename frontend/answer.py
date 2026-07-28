# answer.py — the shape of one answer message: the agent's text, then the footer that names it.
from __future__ import annotations
import html
from .format import SESSION_ID_LABEL_LEN, format_body, meta_bits, title_words
from .htmlsplit import split_html

SEPARATOR = "· · ·"
# Slack so a chunk sized with the pin still fits once the pin is swapped for the footer.
_PIN_MARGIN = 16
# `block` wants the whole answer as one string and lets reply.deliver do the splitting, so it
# calls `frames` with a limit nothing can reach.
_UNBOUNDED = 10 ** 9
# The footer names the session, and three words was too terse to recognise a turn by (Lucas,
# 2026-07-27). Its own char budget too: unlike the /resume picker, a footer line has no bubble
# width to keep stable, so it can afford the whole five words.
TITLE_WORDS = 5
TITLE_CHARS = 48


def _meta_line(provider: str | None, model: str | None, cost_usd: float | None,
               mode: str | None, used: int | None = None, window: int | None = None) -> str:
    bits = meta_bits(provider, model, mode, used, window)
    if cost_usd:
        bits.append(f"${cost_usd:.3f}")
    return " · ".join(bits)


def _session_label(sid: str | None, title: str | None) -> str | None:
    """`[ABC] TÍTULO DA SESSÃO`, or nothing when there is no session to name."""
    result = None
    if sid:
        short = sid[:SESSION_ID_LABEL_LEN].upper()
        words = title_words(title, TITLE_WORDS, TITLE_CHARS)
        result = f"[{short}] {words}"
    return result


def _footer(sid: str | None, title: str | None, provider: str | None, model: str | None,
            cost_usd: float | None, mode: str | None, used: int | None,
            window: int | None) -> list[str]:
    """Two lines, not one (Lucas, 2026-07-27): which session this is, then what it ran on.
    They answer different questions, and running them together made the title hard to find."""
    label = _session_label(sid, title)
    meta = _meta_line(provider, model, cost_usd, mode, used, window)
    return [bit for bit in (label, meta) if bit]


def frames(settled: str, unsettled: str = "", pin: str | None = None,
           footer: list[str] | None = None, limit: int = 4096, soft: int | None = None
           ) -> list[str]:
    """The bubbles an answer occupies right now — mid-stream or finished.

    `settled` is markdown that can no longer change and so is rendered; `unsettled` is the
    tail still arriving, appended as escaped plain text because rendering it would make it
    flicker between literal and formatted as the closing markers land. `pin` (the ⏳ line) rides
    at the very END of the last bubble so it reads as "still going", and the split budget is
    reduced by it so a finished frame can never overflow when the pin is later removed.

    Finished delivery is the degenerate case — no pin, footer present — which is why `block`
    delegates here: the streamed frames and the shipped answer are the same code path, and that
    is what makes the AD-23 non-regression test meaningful rather than a coincidence."""
    rendered = format_body(settled) if settled.strip() else ""
    parts = [rendered]
    if unsettled.strip():
        parts.append(html.escape(unsettled))
    for line in footer or []:
        parts.append(html.escape(line))
    text = "\n".join(part for part in parts if part)
    room = limit - len(pin or "") - _PIN_MARGIN
    chunks = split_html(text, room, soft)
    if pin:
        # A blank line of distance, so the pin reads as a status hanging under the answer rather
        # than as the answer's next line (Lucas, 2026-07-27).
        chunks[-1] = chunks[-1] + "\n\n" + pin
    return chunks


def block(body: str, sid: str | None, title: str | None, provider: str | None = None,
          model: str | None = None, cost_usd: float | None = None,
          mode: str | None = None, context_used: int | None = None,
          context_window: int | None = None) -> str:
    """The agent's answer, then meta: `[ID] TÍTULO · provider · modelo · modo · X% · $custo`.

    F2 led every answer with a `continua [ABC] TÍTULO` line, reasoning that Telegram quotes a
    message from its start, so the session name had to come first. Sound reasoning, wrong
    reader: the bot's answer is already `do_quote`d onto Lucas's own message, so the thread is
    visible without being announced. Lucas, 2026-07-27: *"quando o bot responde a mim, como já
    mostra que é uma resposta, acho que pode deixar assim"*, and *"o título pode ficar no
    rodapé, fica melhor"*. The anchor line is deleted rather than demoted — the id and title
    survive in the footer, which is where he wanted them."""
    footer = _footer(sid, title, provider, model, cost_usd, mode, context_used, context_window)
    tail = [SEPARATOR] + footer
    # Delegates to `frames` at an unbounded limit, so it comes back as exactly one chunk and
    # `reply.deliver` still does the splitting. The point is that the finished answer and a
    # streamed frame are then literally the same code path, which is what makes the AD-23
    # non-regression check meaningful instead of two implementations that merely agree today.
    whole = frames(body, footer=tail, limit=_UNBOUNDED)
    return whole[0]


