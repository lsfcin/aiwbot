# aiwbot — Known Bugs

Log as `- [ ] [bN] <symptom> — <where>`; a FIXED flip needs a `tests/**/b<N>-*`
regression test (see code/VERIFY.md).

## Open
_(none)_ — b1, b2 fixed 2026-07-26; **b3 fixed 2026-07-27** (context % over 100%: the
numerator summed every API request in the turn, so it measured spend, not occupancy). All
archived in [HISTORY.md](HISTORY.md) § Resolved Bugs with their regression specs.


## Residual (by design)
- Bot sessions created **before** 2026-07-23 stay invisible in Claude Code's native picker: the filter
  keys on a session's originating entrypoint, which can't be rewritten after the fact. New sessions are
  fine (`CLAUDE_CODE_ENTRYPOINT=claude-vscode`, SPECS AD-8). For the old ones use the copyable
  `claude --resume <id>` shown in the `/resume` anchor.
