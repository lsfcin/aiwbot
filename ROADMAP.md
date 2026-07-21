# aiwbot — Roadmap

## Context
Provider-agnostic rebuild of the workspace Telegram bot. The old bot (core/tools/telegram_daemon.py)
shells `claude -p` per message (fork/divergence). Official Anthropic Remote Control + Channels solve
sync but lock us 100% into Claude Code — against the provider-agnostic principle. Direction: streaming,
single-lineage, with a swappable backend seam (linuz90's architecture, rebuilt in Python). Providers
become interchangeable data. Full design + research: brain/goals/workspace-os.md.

Phase A (seam proven live) complete — archived in [HISTORY.md](HISTORY.md).

## Phase B — Telegram frontend on the seam (done, unverified live)
- [x] Reuse from core/tools/telegram_daemon.py (provider-agnostic parts): allowlist/config, INBOX $0
      capture, `_safe_reply`/chunking/reply_map, `_format_body` (md→TG-HTML + tables), phrase banks.
      Ported into `frontend/` (own config dir `~/.config/aiwbot/`, own bot handle @lsfaiwbot — not
      shared storage with the old bot). Scope trimmed to `/new` + reply-to-continue + `/help` +
      capture. `/select`/`/notify` deferred — no cross-backend session-listing capability in the
      seam yet; `/stop`/`/status` are obsolete — `send()` is one subprocess call per turn, no
      backgrounded pid to kill/inspect anymore (old bot's `/new` used `claude --bg`).
- [x] Replace claude-specific dispatch with calls through `AgentBackend` (`frontend/dispatch.py`).
      Per-session backend pick via `/new --backend claude|opencode` (default claude).
- [x] Frontend stores latest `result.session_id` each turn (AD-3) — `frontend/sessions.py` registry
      also remembers which backend each session belongs to (no seam equivalent to `claude agents
      --json` exists across providers, so this must be tracked locally).
- [ ] **Live smoke pending** — Lucas to run `python -m frontend.bot` and test `/new`, reply-continue
      (both backends), and plain-text capture end-to-end via @lsfaiwbot before calling Phase B done.

## Phase C — streaming display (linuz90 mold)
- [ ] claude `--output-format stream-json`; edit a "working…" message live with tool status.

## Phase D — persistent mode + more backends
- [ ] claude via SDK `ClaudeSDKClient`, opencode via `--attach` server (only if per-message cost annoys).
- [ ] copilot backend. Retire/thin the workspace bot to INBOX-only capture.

## Verification
- Free (every change): `make test`. Live milestone (~$0.20): `make smoke`.
