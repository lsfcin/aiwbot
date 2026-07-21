# aiwbot — Roadmap

## Context
Provider-agnostic rebuild of the workspace Telegram bot. The old bot (core/tools/telegram_daemon.py)
shells `claude -p` per message (fork/divergence). Official Anthropic Remote Control + Channels solve
sync but lock us 100% into Claude Code — against the provider-agnostic principle. Direction: streaming,
single-lineage, with a swappable backend seam (linuz90's architecture, rebuilt in Python). Providers
become interchangeable data. Full design + research: brain/goals/workspace-os.md.

Phase A (seam proven live) complete — archived in [HISTORY.md](HISTORY.md).

Phase B (Telegram frontend + single-lineage fix + ⏳-morph UX) — done, live-confirmed by Lucas.
Archived in [HISTORY.md](HISTORY.md).

## Niceties (near-term, small each) — in progress
- [ ] **Titles** — kill "(SEM TÍTULO)": derive a session title from the opening prompt
      (provider-agnostic, stored in the sessions registry), carry it forward across turns. Optional
      later: claude's own AI-title read from the transcript (claude-specific).
- [ ] `/select` resume picker — list recent sessions from the registry, tap to resume. Now buildable
      without `claude agents --json` (the registry already knows each session's backend + title).
- [ ] Show the full session id in the reply for manual `claude --resume <id>` / opencode reattach.

## Phase C — streaming display (linuz90 mold)
- [ ] claude `--output-format stream-json`; edit a "working…" message live with tool status.

## Phase D — persistent mode + more backends
- [ ] claude via SDK `ClaudeSDKClient`, opencode via `--attach` server (only if per-message cost annoys).
- [ ] copilot backend. Retire/thin the workspace bot to INBOX-only capture.

## Verification
- Free (every change): `make test`. Live milestone (~$0.20): `make smoke`.
