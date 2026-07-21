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

## Niceties (near-term, small each)
- [x] **Titles** — session title derived from the opening prompt (`format.title_from_prompt`),
      stored in the registry, carried forward across turns. Kills "(SEM TÍTULO)".
- [x] **`/resume` picker** (renamed from `/select`, modeled on Claude Code's resume UI) — inline
      keyboard of recent sessions, each `TÍTULO · <tempo atrás> · backend`, newest-first, count header
      (`N de M`), `/resume <termo>` filters by title. Tap → re-anchors that session as a repliable
      message. Built from the registry (no `claude agents --json`). `frontend/resume.py`. Live-confirmed.
- [x] **Message format** — no intro phrase; answer stands alone with a footer: `<answer>` · `· · ·` ·
      `[XXX] TÍTULO` · `provider · model · $cost`. Model plumbed through the seam (claude from
      `modelUsage`, shortened; opencode degrades to `provider · $cost`). Live-confirmed.
- [ ] **Ghost sessions in `/resume`** — the picker lists pre-title sessions with no title (saved
      before titles existed). Filter untitled entries out of the picker, and/or prune stale registry
      entries (e.g. drop sessions whose transcript no longer exists or older than N days).
- [ ] **`/resume` 3-line buttons** — line 2 = first 6 words … last 6 words of that session's LAST
      agent response. Requires storing the last response text (or a head/tail preview) in the registry
      each turn — the seam already surfaces the text; just persist a preview alongside title/backend.
- [ ] Show the full session id in the reply for manual `claude --resume <id>` / opencode reattach.
- [ ] Pagination past the top 8 in `/resume` (live search-as-you-type impossible in a TG inline
      keyboard, hence `/resume <termo>`).

## Controls — optimized-UX toggles (new, from Lucas 2026-07-21)
- [ ] **plan ↔ build mode** toggle, very low-friction (one tap / short command). Claude Code has a
      plan mode; surface an easy switch so a dispatched turn can run in plan vs build.
- [ ] **model + effort selection** — pick the model and the reasoning effort per session/turn (claude:
      medium/high/…; model family), with optimized UX (tap, not typing flags). Once a real effort
      signal exists, fill the deferred `effort/mode` slot in the footer meta line.

## Input — capture & triggers (new, from Lucas 2026-07-21)
- [ ] **Audio support** — transcribe voice notes → dispatch as a turn (today they only land in INBOX
      untranscribed). If the audio starts with "bot", auto-start a NEW session (`/new`).
- [ ] **"bot"-prefix trigger for text** — a message starting with "bot " or "bot," → treat as `/new`
      (new session) instead of INBOX capture. Same mental model as the audio trigger.

## Phase C — live streaming + interaction (linuz90 mold)
- [ ] **Live feedback** — `stream-json`: edit the message as the agent's chat text arrives, appending
      in chunks, keeping "⏳ pensando…" pinned at the END of the message until the turn finishes.
      (Not everything — just the visible chat text + a live thinking indicator.) Builds on the
      ⏳-morph already shipped.
- [ ] **Interview / ask_user** — let the bot interview Lucas mid-task (essential for plan mode, useful
      elsewhere): agent questions surface as Telegram prompts/inline buttons, answers flow back into
      the running turn. (linuz90's `ask_user` MCP pattern — see [[reference_linuz90_bot]].)

## Phase D — persistent mode + more backends
- [ ] claude via SDK `ClaudeSDKClient`, opencode via `--attach` server (only if per-message cost annoys).
- [ ] copilot backend. Retire/thin the workspace bot to INBOX-only capture.

## Verification
- Free (every change): `make test`. Live milestone (~$0.20): `make smoke`.
