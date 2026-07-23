# aiwbot — Known Bugs

Log as `- [ ] [bN] <symptom> — <where>`; a FIXED flip needs a `tests/**/b<N>-*`
regression test (see code/VERIFY.md).

## Won't-fix (external constraints)
- Bot `-p` sessions never appear in Claude Code's **native** `/resume` (VSCode/terminal) — the CLI
  stamps `entrypoint:"sdk-cli"` on headless turns and the closed picker filters those out (proven by
  diffing the picker's list against the store; `--name` writes a `custom-title` but does not surface).
  Not fixable from outside the extension. **Workaround, verified:** they resume fine by explicit id —
  the bot's `/resume` anchor shows a copyable `claude --resume <id>`. See SPECS AD-8.
