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

## Residual (by design)
- Bot sessions created **before** 2026-07-23 stay invisible in Claude Code's native picker: the filter
  keys on a session's originating entrypoint, which can't be rewritten after the fact. New sessions are
  fine (`CLAUDE_CODE_ENTRYPOINT=claude-vscode`, SPECS AD-8). For the old ones use the copyable
  `claude --resume <id>` shown in the `/resume` anchor.
