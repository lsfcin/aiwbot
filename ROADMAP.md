# aiwbot — Roadmap

## Context
Provider-agnostic rebuild of the workspace Telegram bot. The old bot (core/tools/telegram_daemon.py)
shells `claude -p` per message (fork/divergence). Official Anthropic Remote Control + Channels solve
sync but lock us 100% into Claude Code — against the provider-agnostic principle. Direction: streaming,
single-lineage, with a swappable backend seam (linuz90's architecture, rebuilt in Python). Providers
become interchangeable data. Full design + research: brain/goals/workspace-os.md.

Phase A (seam proven live) complete — archived in [HISTORY.md](HISTORY.md).

## Phase B — Telegram frontend on the seam (next)
- [ ] Reuse from core/tools/telegram_daemon.py (provider-agnostic parts): allowlist/config, INBOX $0
      capture, `_safe_reply`/chunking/reply_map, `_format_body` (md→TG-HTML + tables), phrase banks.
- [ ] Replace claude-specific dispatch with calls through `AgentBackend`. Per-session backend pick.
- [ ] Frontend stores latest `result.session_id` each turn (AD-3).

## Phase C — streaming display (linuz90 mold)
- [ ] claude `--output-format stream-json`; edit a "working…" message live with tool status.

## Phase D — persistent mode + more backends
- [ ] claude via SDK `ClaudeSDKClient`, opencode via `--attach` server (only if per-message cost annoys).
- [ ] copilot backend. Retire/thin the workspace bot to INBOX-only capture.

## Verification
- Free (every change): `make test`. Live milestone (~$0.20): `make smoke`.
