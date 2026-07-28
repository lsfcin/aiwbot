# answer.py — the shape of one answer message: the agent's text, then the footer that names it.
from __future__ import annotations
import html
from .format import SESSION_ID_LABEL_LEN, format_body, meta_bits, title_words

SEPARATOR = "· · ·"
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
    lines = []
    formatted = format_body(body)
    lines.append(formatted)
    lines.append(SEPARATOR)
    footer = _footer(sid, title, provider, model, cost_usd, mode, context_used, context_window)
    for line in footer:
        escaped = html.escape(line)
        lines.append(escaped)
    return "\n".join(lines)
