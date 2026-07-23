# aiwbot — Known Bugs

Log as `- [ ] [bN] <symptom> — <where>`; a FIXED flip needs a `tests/**/b<N>-*`
regression test (see code/VERIFY.md).

## Won't-fix (external constraints)
- Bot `-p` sessions never appear in Claude Code's **native** `/resume` (VSCode/terminal) — the CLI
  stamps `entrypoint:"sdk-cli"` on headless turns and the closed picker filters those out. Not
  fixable from outside the extension. Use the bot's own `/resume`. See SPECS AD-8.
