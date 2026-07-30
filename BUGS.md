# aiwbot — Known Bugs

Log as `- [ ] [bN] <symptom> — <where>`; a FIXED flip needs a `tests/**/b<N>-*`
regression test (see code/VERIFY.md).

## Open
- [x] **[b4] FIXED 2026-07-29 — every opencode turn ran in the daemon's LAUNCH directory, not the
      workspace.** Found while checking opencode streaming: a turn given
      `cwd=/mnt/workspace` reported `pwd` as the directory its parent process happened to be in.
      Cause: opencode trusts **`PWD`** over its real working directory, and `PWD` was inherited from
      the daemon — so with the daemon started from `/home/lucas`, its file and shell tools worked
      there AND the session was FILED there, while `/resume` (which lists per directory) asked for
      `/mnt/workspace` and never showed it. Visible in the store as Lucas's own Telegram prompts
      filed under `/home/lucas`: *"oi"*, *"teste, tá funcionando?"*, *"claudsonner me ajuda a
      procurar um chuveiro"*. Fix: `proc.child_env` forces `PWD` to the turn's cwd for every child,
      after the backend's own knobs, so no provider can disagree with the seam.
      Spec: `tests/test_b4_opencode_cwd.py`. claude was never affected (it uses its real cwd), but
      it is pinned the same way — the driver owns this, not one backend's override.
      **The running daemon keeps the old behaviour until it is restarted.**

Earlier: b1, b2 fixed 2026-07-26; **b3 fixed 2026-07-27** (context % over 100%: the
numerator summed every API request in the turn, so it measured spend, not occupancy). Each has
its regression spec under `tests/test_b<N>_*.py`.


## Residual (by design)
- The eight opencode sessions b4 filed under `/home/lucas` stay out of `/resume`, which lists per
  directory and cannot rewrite where a session was recorded. They are reachable from a terminal
  (`opencode` in that directory, then its own picker). Turns from 2026-07-29 on are filed correctly.
- Bot sessions created **before** 2026-07-23 stay invisible in Claude Code's native picker: the filter
  keys on a session's originating entrypoint, which can't be rewritten after the fact. New sessions are
  fine (`CLAUDE_CODE_ENTRYPOINT=claude-vscode`, SPECS AD-8). For the old ones use the copyable
  `claude --resume <id>` shown in the `/resume` anchor.
