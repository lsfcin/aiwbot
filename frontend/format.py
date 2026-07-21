# format.py — pure text formatting: markdown/tables -> Telegram HTML, session headers. No I/O.
from __future__ import annotations
import html
import re
import time

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


def _is_table_row(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and s.endswith("|") and s.count("|") >= 2


def _is_table_sep(line: str) -> bool:
    s = line.strip()
    core = s.strip("|").strip()
    result = False
    if core:
        cells = [c.strip() for c in core.split("|")]
        result = all(c and set(c) <= set("-:") and "-" in c for c in cells)
    return result


def _convert_inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`\n]+?)`", r"<code>\1</code>", text)
    return text


def _format_text_chunk(text: str) -> str:
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        if _is_table_row(lines[i]) and i + 1 < len(lines) and _is_table_sep(lines[i + 1]):
            block = [lines[i], lines[i + 1]]
            j = i + 2
            while j < len(lines) and _is_table_row(lines[j]):
                block.append(lines[j])
                j += 1
            out.append(f"<pre>{html.escape(chr(10).join(block))}</pre>")
            i = j
        else:
            out.append(_convert_inline(lines[i]))
            i += 1
    return "\n".join(out)


def format_body(text: str) -> str:
    # Telegram has no table syntax at all — pipe-tables get boxed as monospace <pre>.
    out, last = [], 0
    for m in re.finditer(r"```(?:\w+\n)?(.*?)```", text, flags=re.S):
        out.append(_format_text_chunk(text[last:m.start()]))
        out.append(f"<pre>{html.escape(m.group(1))}</pre>")
        last = m.end()
    out.append(_format_text_chunk(text[last:]))
    return "".join(out)


def session_block(phrase: str, sid: str | None, title: str | None, body: str | None = None, extra: str | None = None) -> str:
    lines = [html.escape(phrase)]
    if sid:
        header = f"[{sid[:SESSION_ID_LABEL_LEN].upper()}] {title_words(title)}"
        if extra:
            header += f" · {extra}"
        lines.append(html.escape(header))
    if body:
        lines.append(format_body(body))
    return "\n".join(lines)
