# aiwbot — Known Bugs

Log as `- [ ] [bN] <symptom> — <where>`; a FIXED flip needs a `tests/**/b<N>-*`
regression test (see code/VERIFY.md).

## Open
- [ ] **[b3] context occupancy reports impossible percentages** — the `X%` in an answer's meta
  footer "passa de 100%, em alguns casos passando de 200%" (Lucas, INBOX 2026-07-26). Since the
  number is a share of the window it cannot exceed 100% by definition, so either the numerator is
  a lifetime sum rather than a per-message occupancy, or the window is wrong for the model that
  actually ran. Both are live suspects and neither is confirmed:
  `format.context_pct(used, window)` divides whatever it is handed; `ocstore.context_used`
  deliberately reads per-message `tokens.input + cache.read + cache.write` *because* the session's
  `tokens_*` columns accumulate (one real session summed to 175% of its window — see the comment
  in `ocstore.py`, which means this exact failure was already understood once); and
  `registry.remember_context_window` *learns* the window from a live turn, so one bad observation
  poisons every later percentage for that model. Start by logging the raw pair, not the quotient.
  Touches `frontend/format.py`, `backend/ocstore.py`, `backend/transcript.py`, `frontend/registry.py`.

## Residual (by design)
- Bot sessions created **before** 2026-07-23 stay invisible in Claude Code's native picker: the filter
  keys on a session's originating entrypoint, which can't be rewritten after the fact. New sessions are
  fine (`CLAUDE_CODE_ENTRYPOINT=claude-vscode`, SPECS AD-8). For the old ones use the copyable
  `claude --resume <id>` shown in the `/resume` anchor.
