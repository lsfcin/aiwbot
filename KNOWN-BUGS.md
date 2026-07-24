# aiwbot — Known Bugs

Log as `- [ ] [bN] <symptom> — <where>`; a FIXED flip needs a `tests/**/b<N>-*`
regression test (see code/VERIFY.md).

## Open
- [ ] [b1] **tables and bold don't render** in bot messages — reported still broken 2026-07-24
  (`— via aiwbot`, so the answer text itself was affected). Conversion path is
  `frontend/markdown.py` (block: fences, tables, headings) + `frontend/inline.py` (bold, code,
  links). A FIXED flip needs a `tests/**/b1-*` regression spec (code/VERIFY.md). Likely the
  Telegram-HTML escaping order or the pipe-table detector; verify against a real answer, not a
  hand-written fixture.

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

## Residual (by design)
- Bot sessions created **before** 2026-07-23 stay invisible in Claude Code's native picker: the filter
  keys on a session's originating entrypoint, which can't be rewritten after the fact. New sessions are
  fine (`CLAUDE_CODE_ENTRYPOINT=claude-vscode`, SPECS AD-8). For the old ones use the copyable
  `claude --resume <id>` shown in the `/resume` anchor.
