# aiwbot — Known Bugs

Log as `- [ ] [bN] <symptom> — <where>`; a FIXED flip needs a `tests/**/b<N>-*`
regression test (see code/VERIFY.md).

## Open
- [ ] [b2] **opencode backend errors collapse to generic "no text event"** — reported 2026-07-24.
  Confirmed root cause of that specific report: nvidia free-tier `deepseek-v4-flash` rate limit
  (`ResourceExhausted: Worker local total request limit reached (48/48)`, visible in opencode's
  own sqlite `message.data.error`, session `ses_069a2c935ffe57KwNcyj0cEOrF`) — NOT an audio-feature
  bug; the CLI exited 0 with stdout `proc.py` didn't treat as a hard-fail, so `events_from_run`
  handed it to `opencode.py`'s `parse_events`, whose `_line_to_event` only recognizes
  `type=="text"`/`type=="step_finish"` — an error-shaped line falls through silently, producing
  zero events, hence `check_contract`'s generic `"no text event"` instead of the real reason.
  Fix needs the actual raw CLI stdout JSON shape for an error turn to parse correctly — two live
  repro attempts both hung (`opencode run ... -s <sid>` timed out with no output), so the exact
  shape is still unconfirmed; don't guess-patch `_line_to_event` blind. A FIXED flip needs a
  `tests/**/b2-*` regression fixture built from a real captured error payload.

## Fixed
- [x] [b1] **tables and bold don't render** — FIXED 2026-07-26. The hunch in the original entry
  (escaping order / the pipe-table detector) was wrong; escaping was correct throughout. Probing
  4000 real assistant answers from `~/.claude/projects` found **two independent causes**, which is
  why the one report named two symptoms:
  1. **Tables.** `markdown._table_block` boxed every table in `<pre>`, which escapes its contents —
     so cell markdown froze into literal `**`. Measured over the 412 tables in those answers:
     **95% carried inline markdown**, and **0 of 412** fit a phone-width monospace bubble (median
     widest row 151 chars), so the box also overflowed. No narrow case existed to preserve; `<pre>`
     boxing is gone, replaced by `frontend/table.py` rendering rows as labelled blocks.
  2. **Bold.** `_BOLD_RE`'s non-greedy close took the first two of the three trailing asterisks in
     `**bold *italic***`, leaving `<b>x <i>y</b></i>`. Telegram rejects crossed entities, and
     `reply._send_plain` then strips **every** tag — so one such run cost the whole message its
     formatting. Fixed with a `(?!\*)` lookahead on the close.
  Regression spec: `tests/test_b1_table_bold.py`. Same 4000-answer probe now reports 0 rejections.

## Residual (by design)
- Bot sessions created **before** 2026-07-23 stay invisible in Claude Code's native picker: the filter
  keys on a session's originating entrypoint, which can't be rewritten after the fact. New sessions are
  fine (`CLAUDE_CODE_ENTRYPOINT=claude-vscode`, SPECS AD-8). For the old ones use the copyable
  `claude --resume <id>` shown in the `/resume` anchor.
