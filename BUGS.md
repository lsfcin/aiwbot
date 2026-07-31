# aiwbot — Known Bugs

Log as `- [ ] [bN] <symptom> — <where>`; a FIXED flip needs a `tests/**/b<N>-*`
regression test (see code/VERIFY.md).

## Open
_(none.)_ b1, b2 fixed 2026-07-26; b3 2026-07-27 (context % measured spend, not occupancy);
**b4 2026-07-29, live since the daemon restart** — opencode trusts `$PWD` over its real working
directory, so every Telegram turn ran its tools in the daemon's launch directory and filed its
session there. Each has its regression spec under `tests/test_b<N>_*.py`.


## Residual (by design)
- The eight opencode sessions b4 filed under `/home/lucas` stay out of `/resume`, which lists per
  directory and cannot rewrite where a session was recorded. They are reachable from a terminal
  (`opencode` in that directory, then its own picker). Turns from 2026-07-29 on are filed correctly.
- Bot sessions created **before** 2026-07-23 stay invisible in Claude Code's native picker: the filter
  keys on a session's originating entrypoint, which can't be rewritten after the fact. New sessions are
  fine (`CLAUDE_CODE_ENTRYPOINT=claude-vscode`, SPECS AD-8). For the old ones use the copyable
  `claude --resume <id>` shown in the `/resume` anchor.
