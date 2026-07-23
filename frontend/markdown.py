# markdown.py — agent markdown -> Telegram HTML: block level (fences, tables, headings, lists).
from __future__ import annotations
import html
import re
from .inline import convert

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET_RE = re.compile(r"^(\s*)[-*+]\s+(.*)$")
_NUMBER_RE = re.compile(r"^(\s*)(\d+)\.\s+(.*)$")
_QUOTE_RE = re.compile(r"^>\s?(.*)$")
_RULE_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")

# Telegram has no headings, so hierarchy is carried by weight: # and ## shout, ### and
# deeper are plain bold. Two levels is all a chat bubble can legibly hold.
_CAPS_LEVEL = 2
_HR = "─────"
_BULLETS = ("•", "◦")
_NEST_INDENT = 2


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


def _heading(match: re.Match) -> str:
    """Uppercasing happens before conversion — after it, .upper() would hit the tag names."""
    hashes = match.group(1)
    body = match.group(2)
    level = len(hashes)
    if level <= _CAPS_LEVEL:
        body = body.upper()
    text = convert(body)
    return f"<b>{text}</b>"


def _bullet(match: re.Match) -> str:
    indent = match.group(1)
    body = match.group(2)
    depth = len(indent) // _NEST_INDENT
    last = len(_BULLETS) - 1
    index = min(depth, last)
    glyph = _BULLETS[index]
    text = convert(body)
    return f"{indent}{glyph}  {text}"


def _numbered(match: re.Match) -> str:
    indent = match.group(1)
    number = match.group(2)
    body = match.group(3)
    text = convert(body)
    return f"{indent}{number}.  {text}"


def _quote(match: re.Match) -> str:
    body = match.group(1)
    text = convert(body)
    return f"<blockquote>{text}</blockquote>"


_LINE_RULES = ((_HEADING_RE, _heading), (_BULLET_RE, _bullet),
               (_NUMBER_RE, _numbered), (_QUOTE_RE, _quote))


def _convert_line(line: str) -> str:
    """First matching block rule wins; anything unmatched is plain inline markdown."""
    result = None
    ruled = _RULE_RE.match(line)
    if ruled:
        result = _HR
    else:
        for pattern, handler in _LINE_RULES:
            hit = pattern.match(line)
            if hit:
                result = handler(hit)
                break
    if result is None:
        result = convert(line)
    return result


def _table_block(lines: list[str], start: int) -> tuple[str, int]:
    """A header row plus its `---` separator opens a table; it runs until a non-row line."""
    block = [lines[start], lines[start + 1]]
    j = start + 2
    while j < len(lines) and _is_table_row(lines[j]):
        block.append(lines[j])
        j += 1
    body = "\n".join(block)
    escaped = html.escape(body)
    return f"<pre>{escaped}</pre>", j


def _format_text_chunk(text: str) -> str:
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        if _is_table_row(lines[i]) and i + 1 < len(lines) and _is_table_sep(lines[i + 1]):
            rendered, i = _table_block(lines, i)
            out.append(rendered)
        else:
            converted = _convert_line(lines[i])
            out.append(converted)
            i += 1
    return "\n".join(out)


def format_body(text: str) -> str:
    # Telegram has no table syntax at all — pipe-tables get boxed as monospace <pre>.
    out, last = [], 0
    for m in re.finditer(r"```(?:\w+\n)?(.*?)```", text, flags=re.S):
        chunk = _format_text_chunk(text[last:m.start()])
        out.append(chunk)
        fenced = html.escape(m.group(1))
        out.append(f"<pre>{fenced}</pre>")
        last = m.end()
    tail = _format_text_chunk(text[last:])
    out.append(tail)
    return "".join(out)
