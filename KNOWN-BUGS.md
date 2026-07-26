# aiwbot — Known Bugs

Log as `- [ ] [bN] <symptom> — <where>`; a FIXED flip needs a `tests/**/b<N>-*`
regression test (see code/VERIFY.md).

## Open
_(none)_

## Fixed
- [x] [b2] **opencode backend errors collapse to generic "no text event"** — FIXED 2026-07-26.
  The previous entry's analysis was right and only the payload shape was missing. Earlier repro
  attempts hung because they resumed a session (`opencode run … -s <sid>`); forcing the error on a
  *fresh* run returns instantly:
  ```
  opencode run "hi" --format json -m "nvidia/definitely-not-a-real-model"
  {"type":"error","timestamp":…,"sessionID":"ses_…","error":{"name":"UnknownError",
   "data":{"message":"Unexpected server error. Check server logs for details.","ref":"err_c1ecc11d"}}}
  ```
  Exit code **0**, confirming why `proc.py` never treated it as a hard fail. Two changes:
  `_line_to_event` now maps `type=="error"` to an error event, preferring `error.data.message`
  (opencode labels everything `UnknownError`, so the outer name is worthless) and degrading to the
  name, then the raw object. Separately `events_from_run` treats a parse yielding **zero** events
  as a failure in its own right and quotes the raw stdout/stderr tail — so the next unrecognized
  shape names itself instead of repeating this investigation.
  Regression spec: `tests/test_b2_opencode_error.py` + `tests/fixtures/opencode_error.jsonl`
  (the captured payload above, verbatim).
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
