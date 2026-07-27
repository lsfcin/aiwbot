# aiwbot — Known Bugs

Log as `- [ ] [bN] <symptom> — <where>`; a FIXED flip needs a `tests/**/b<N>-*`
regression test (see code/VERIFY.md).

## Open
_(none)_ — b1, b2 fixed 2026-07-26; **b3 fixed 2026-07-27**, all archived in
[HISTORY.md](HISTORY.md) § Resolved Bugs with their regression specs.

- [x] **[b3] context occupancy reported impossible percentages** (Lucas, INBOX 2026-07-26:
  "passando de 100%, em alguns casos passando de 200%") — **FIXED**, spec
  `tests/test_b3_context_pct.py`. The denominator was innocent: the learned windows were a
  correct 1,000,000. The numerator was a **sum over every API request in the turn**. A turn that
  uses tools makes several requests and each re-reads the whole context from cache, so
  `modelUsage`'s token fields measure *spend*, not how full the window is. Measured over real
  transcripts the sums reach 5921%, 6507%, 32533% — and, worse, sometimes land on a
  plausible-looking 62% that was really 5%. Occupancy is a property of the LAST request alone, so
  it now comes from each provider's own per-message store through a new `CliBackend.occupancy()`
  seam (claude: the transcript's last assistant message; opencode: `ocstore.last_turn`, which
  also means an opencode answer reports a % at all for the first time). `format.context_pct`
  additionally withholds any share above 100%, since such a pair cannot be true.
  `ocstore.py` had already documented this exact trap for opencode's `tokens_*` columns; the
  claude path walked into it anyway, which is why the seam now owns the rule instead of one
  backend remembering it.

## Residual (by design)
- Bot sessions created **before** 2026-07-23 stay invisible in Claude Code's native picker: the filter
  keys on a session's originating entrypoint, which can't be rewritten after the fact. New sessions are
  fine (`CLAUDE_CODE_ENTRYPOINT=claude-vscode`, SPECS AD-8). For the old ones use the copyable
  `claude --resume <id>` shown in the `/resume` anchor.
