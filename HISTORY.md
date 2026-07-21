# aiwbot — History
> Archive of completed work. Open work lives in [ROADMAP.md](ROADMAP.md).

## Completed — 2026-07-21

### Phase B — Telegram frontend on the seam (live-confirmed)
- `frontend/` on the AgentBackend seam: `/new [--backend claude|opencode]`, reply-to-continue,
  plain text/media → brain/INBOX.md capture, `/help`. Own config dir `~/.config/aiwbot/`, own bot
  handle @lsfaiwbot. Reuses old-bot plumbing (config shape, md→TG-HTML formatting, phrase banks).
- New `frontend/sessions.py` registry tracks session_id→backend locally — there's no cross-backend
  `claude agents --json` equivalent, so the frontend must remember which backend owns each session.
- Scope trimmed vs the old bot: `/select`/`/notify` deferred (need cross-backend session listing),
  `/stop`/`/status` dropped (obsolete — `send()` is one subprocess call per turn, no `--bg` pid).
- **Single-lineage fix**: dropped claude's `--fork-session` → plain `--resume`. The fork (stale AD-3,
  from the old `--bg` era) was minting a new session id per turn and piling up cumulative VSCode
  session entries. Plain resume keeps one id / one transcript / one VSCode entry that grows in place
  — verified live (3 chained turns, same id, context kept). Matches linuz90's SDK design
  ([[reference_linuz90_bot]]). Graceful "session live elsewhere in VSCode" message for the
  concurrent-edit edge.
- **⏳-morph UX**: the "trabalhando…" placeholder is edited in place into the final answer (feels
  like a substitution), not left as a separate message. Seed of Phase C streaming.
- Verify: 16 free tests green (`make test`). Live-confirmed by Lucas via @lsfaiwbot (single lineage,
  full conversations visible in VSCode). Gitflow: `feature/telegram-frontend` → merged to `develop`.

### Phase A — prove the provider-agnostic seam
- `AgentBackend`/`AgentEvent` seam + `CliBackend` driver + `check_contract` (backend/base.py, cli.py).
- `claude` + `opencode` backends: `build_args` + pure `parse_events` (backend/claude.py, opencode.py).
- Free fixture unit tests — 6 green (`make test`, tests/).
- Live smoke (`make smoke`): both backends pass end-to-end + single-lineage resume. **Risk retired** —
  the one interface holds across a forking backend (claude, `--fork-session`, new id/turn) and a
  same-lineage backend (opencode, `-s`, same id). Frontend chases `result.session_id` (AD-3, SPECS.md).
- Gitflow: scaffold on `main` → Phase A on `feature/agent-backend-seam` → merged to `develop`.
