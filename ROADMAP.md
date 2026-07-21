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
- [x] **Titles** — session title derived from the opening prompt (`format.title_from_prompt`),
      stored in the registry, carried forward across turns. Kills "(SEM TÍTULO)". Optional later:
      claude's own AI-title read from the transcript (claude-specific).
- [x] **`/resume` picker** (renamed from `/select`, modeled on Claude Code's resume UI) — inline
      keyboard of recent sessions, each `TÍTULO · <tempo atrás> · backend`, newest-first, count header
      (`N de M`), `/resume <termo>` filters by title (approximates Claude Code's search box). Tap →
      re-anchors that session as a repliable message (reply to continue). Built from the registry —
      no `claude agents --json` needed. `frontend/resume.py`. Live-confirm pending.
- [ ] Show the full session id in the reply for manual `claude --resume <id>` / opencode reattach.
- [ ] Later, from Claude Code's picker: pagination past the top 8; live search-as-you-type isn't
      possible in a Telegram inline keyboard (hence `/resume <termo>`).

## Phase C — streaming display (linuz90 mold)
- [ ] claude `--output-format stream-json`; edit a "working…" message live with tool status.

## Phase D — persistent mode + more backends
- [ ] claude via SDK `ClaudeSDKClient`, opencode via `--attach` server (only if per-message cost annoys).
- [ ] copilot backend. Retire/thin the workspace bot to INBOX-only capture.

## Verification
- Free (every change): `make test`. Live milestone (~$0.20): `make smoke`.
