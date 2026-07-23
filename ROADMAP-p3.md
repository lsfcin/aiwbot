# aiwbot — P3: Telegram output fidelity + `/resume` stability

Sub-roadmap of [ROADMAP.md](ROADMAP.md) § P3. Design decisions and traps for the round in progress.

## Why
Three problems sharing one root: what the agent writes is not what Telegram renders. Ships first
because it is cheap and touches every single message.

## Decisions (Lucas, 2026-07-23)
| question | chosen | over |
|---|---|---|
| inactive `‹`/`›` slot | **inert arrow** — glyph always shown, edge tap does nothing | dimmed `·`, wrap-around |
| bubble width | **char budgets + invisible ruler** — guaranteed constant width | budgets alone, buttons alone |
| `#`/`##` headings | **bold caps**, `###`+ plain bold — two visible levels | bold-only, glyph prefix |
| scope | markdown + HTML-safe delivery + `/resume` | opencode parity moved to P2 |

## Part 1 — markdown gaps (`frontend/markdown.py`)
Extend `format_body`; keep its ordering (fences extracted first, then block handling, then inline) —
that is what protects code content.

**Structural fix first.** `_convert_inline` runs its regexes over the whole string, so markdown *inside*
an inline code span gets converted. Tokenize: pull code spans to placeholders, convert, restore. Every
rule below then composes safely.

Block level, per line, before inline conversion:

| markdown | renders as | note |
|---|---|---|
| `#`, `##` | `<b>` + `.upper()` | PT accents survive `.upper()` |
| `###`+ | `<b>` plain case | second and last level of hierarchy |
| `- x`, `* x`, `+ x` | `•  x` | indent ≥2 → `◦  x` |
| `1. x` | `1.  x` | number kept, spacing normalized |
| `> x` | `<blockquote>` | Telegram supports it natively |
| `---` | `─────` | **not** `· · ·` — that is the answer-footer separator |

Inline order after `html.escape`: `**bold**` → `~~strike~~` → code spans (already extracted) →
`[text](url)` → `*italic*`/`_italic_`.
- Italic runs after bold and requires non-`*` neighbours, or `**x**` gets eaten.
- Links: `<a href="…">`, URL attribute-escaped, `http`/`https`/`tg` only. Bare URLs left alone —
  Telegram auto-links them.

**Size guard**: 56 LOC now, hard gate 200. Past ~160, split inline conversion into `frontend/inline.py`.
R5 (≤40 lines/function) pushes the block dispatcher toward a table of line-matchers, not an if-chain.

## Part 2 — HTML-safe delivery (`frontend/htmlsplit.py` new, `frontend/reply.py`)
- `split_html(text, limit)` — split on line boundaries, never mid-line; carry a tag stack so anything
  open at a boundary is closed at the chunk end and reopened at the next chunk's start. One line longer
  than the limit is the only hard split, done inside `<pre>`.
- `strip_tags(text)` — the fallback body.
- `reply._chunks` → `split_html`. `safe_reply` gains a last resort: on an entity/parse error, resend
  once with `parse_mode=None` over `strip_tags(...)`. **A degraded message beats a silent drop.**

## Part 3 — `/resume` stability (`frontend/resume.py`, `frontend/format.py`)
- **Fixed 5 slots.** `_keyboard` always emits `‹ N N N ›`; at the ends `callback_data="noop:"` and the
  handler answers silently (dismisses the spinner, nothing else). Register `noop` in `bot.py`'s pattern:
  `^(resume|page|noop):`. *If a dead tap reads as broken live, a one-word toast in `query.answer()` is a
  one-line change — left out deliberately per the chosen option.*
- **Char budgets.** New pure `format.clip_chars(text, limit)` (ellipsis `…`) applied inside the existing
  `title_words` and `response_preview`; word caps stay, char clip rides on top, so `session_block` and
  `answer_block` inherit stable widths with no signature change. Title ≤32, preview ≤64.
- **Width ruler.** `<code>`-wrapped run of `RULER_WIDTH` non-breaking spaces, last line of the header
  block. Monospace makes the width predictable; NBSP survives client-side trimming.
  **Trap:** `_page` returns `format.plain(text)`, which escapes the whole picker string — inject the
  ruler *after* that escape or its tags become literal text. `RULER_WIDTH = 0` is the kill switch.
- **Drop `/resume N`.** `_parse_arg` reads a bare number as a page size while `_turn_page` hardcodes 3,
  so page 1 shows 1-5 and page 2 shows 4-6 — one numeral naming two sessions, which is exactly what
  AD-5 exists to prevent. `HELP_TEXT` only ever documented `/resume [busca]`. Pagination is always 3 and
  `/resume 2026` becomes a real title filter.
- **Mode toggle on anchors.** `_anchor` sends a repliable message with no BUILD/PLAN button. Attach
  `mode.toggle_markup(sid, sessions.mode_for(sid))` — both helpers already exist.

## Verification
**Free:** `make test`. New `tests/test_markdown.py` (keeps `test_format.py` small): one test per
conversion rule; `split_html` closing/reopening tags across a boundary; `strip_tags`; `clip_chars` at
and under the limit; keyboard always 5 buttons with `noop:` at each end; `_parse_arg` treating a digit
string as a filter.

**Live, Lucas's eyeball on the phone** (none of these are provable from a test):
1. Heading-heavy answer → `##` reads as bold caps, `-` as bullets.
2. Answer >4096 chars → arrives whole, no broken formatting at the split.
3. Page `/resume` across ≥3 pages → bubble stops resizing.
4. Ruler is invisible, not a grey monospace bar. If it shows → `RULER_WIDTH = 0`.
