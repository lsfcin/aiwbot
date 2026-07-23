# format.py — pure text formatting: markdown/tables -> Telegram HTML, session headers. No I/O.
from __future__ import annotations
import html
import time
from .markdown import format_body

SESSION_ID_LABEL_LEN = 3


def relative_time(ts: float, now: float | None = None) -> str:
    """Human relative age like Claude Code's resume picker: agora / 5m atrás / 2h atrás / 3d atrás."""
    ref = now
    if ref is None:
        ref = time.time()
    delta = ref - ts
    result = "agora"
    if delta >= 86400:
        days = int(delta // 86400)
        result = f"{days}d atrás"
    elif delta >= 3600:
        hours = int(delta // 3600)
        result = f"{hours}h atrás"
    elif delta >= 60:
        mins = int(delta // 60)
        result = f"{mins}m atrás"
    return result


def plain(text: str) -> str:
    return html.escape(text)


def title_words(name: str | None, n: int = 3) -> str:
    result = "(SEM TÍTULO)"
    if name and name.strip():
        result = " ".join(name.split()[:n]).upper()
    return result


def title_from_prompt(prompt: str, n: int = 8) -> str:
    """Provider-agnostic session title: the first few words of the opening prompt."""
    words = prompt.split()
    return " ".join(words[:n])


def response_preview(text: str, n: int = 6) -> str:
    """First n … last n words of a response, for the /resume picker preview line."""
    words = text.split()
    result = " ".join(words)
    if len(words) > 2 * n:
        head = " ".join(words[:n])
        tail = " ".join(words[-n:])
        result = f"{head} … {tail}"
    return result


# Provider as data: how each backend re-opens a session by id outside the bot.
_REATTACH = {"claude": "claude --resume {sid}", "opencode": "opencode -s {sid}"}


def reattach_cmd(sid: str, backend: str | None = None) -> str | None:
    """Copy-paste command to reopen a session in the terminal/VSCode. Bot `-p` sessions are
    resumable by id but never listed in Claude Code's own picker (SPECS AD-8), so the id is
    the only way out of the bot. None for a backend we don't know how to reattach."""
    key = backend or ""
    template = _REATTACH.get(key)
    result = None
    if template:
        result = template.format(sid=sid)
    return result


def session_block(phrase: str, sid: str | None, title: str | None, body: str | None = None,
                  extra: str | None = None, backend: str | None = None) -> str:
    lines = [html.escape(phrase)]
    if sid:
        header = f"[{sid[:SESSION_ID_LABEL_LEN].upper()}] {title_words(title)}"
        if extra:
            header += f" · {extra}"
        lines.append(html.escape(header))
        cmd = reattach_cmd(sid, backend)
        if cmd:
            escaped = html.escape(cmd)
            lines.append(f"<code>{escaped}</code>")
    if body:
        lines.append(format_body(body))
    return "\n".join(lines)


_MODEL_FAMILIES = ("sonnet", "opus", "haiku", "fable")


def short_model(model: str | None) -> str | None:
    """claude-sonnet-5 -> sonnet; unknown families fall back to the raw string."""
    result = model
    if model:
        for family in _MODEL_FAMILIES:
            if family in model:
                result = family
                break
    return result


def context_pct(used: int | None, window: int | None) -> str | None:
    """Context occupancy as `32%`. None unless the provider reported both numbers —
    claude gets them free from the result object's modelUsage (no extra tokens)."""
    result = None
    if used and window:
        ratio = 100 * used / window
        pct = round(ratio)
        result = f"{pct}%"
    return result


def meta_bits(provider: str | None, model: str | None, mode: str | None,
              used: int | None = None, window: int | None = None) -> list[str]:
    """Shared head of every meta line: provider · modelo · modo · X%. Callers append
    the tail that differs — `$custo` on answers, `quando` on the /resume list."""
    bits = []
    if provider:
        bits.append(provider)
    short = short_model(model)
    if short:
        bits.append(short)
    if mode:
        bits.append(mode)
    pct = context_pct(used, window)
    if pct:
        bits.append(pct)
    return bits


def _meta_line(provider: str | None, model: str | None, cost_usd: float | None,
               mode: str | None, used: int | None = None, window: int | None = None) -> str:
    bits = meta_bits(provider, model, mode, used, window)
    if cost_usd:
        bits.append(f"${cost_usd:.3f}")
    return " · ".join(bits)


def answer_block(body: str, sid: str | None, title: str | None, provider: str | None = None,
                 model: str | None = None, cost_usd: float | None = None,
                 mode: str | None = None, context_used: int | None = None,
                 context_window: int | None = None) -> str:
    """The network's answer with the session header as a footer (everything here is a response).
    Footer meta reads provider · modelo · modo · X%contexto · $custo."""
    lines = [format_body(body), "· · ·"]
    if sid:
        label = f"[{sid[:SESSION_ID_LABEL_LEN].upper()}] {title_words(title)}"
        lines.append(html.escape(label))
    meta = _meta_line(provider, model, cost_usd, mode, context_used, context_window)
    if meta:
        lines.append(html.escape(meta))
    return "\n".join(lines)
