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

## Shipped
- [x] **Titles** — session title derived from the opening prompt (`format.title_from_prompt`),
      stored in the registry, carried forward across turns. Kills "(SEM TÍTULO)".
- [x] **`/resume` picker** (renamed from `/select`, modeled on Claude Code's resume UI) — inline
      keyboard of recent sessions, each `TÍTULO · <tempo atrás> · backend`, newest-first, count header
      (`N de M`), `/resume <termo>` filters by title. Tap → re-anchors that session as a repliable
      message. Built from the registry (no `claude agents --json`). `frontend/resume.py`. Live-confirmed.
- [x] **Message format** — no intro phrase; answer stands alone with a footer: `<answer>` · `· · ·` ·
      `[XXX] TÍTULO` · `provider · model · $cost`. Model plumbed through the seam (claude from
      `modelUsage`, shortened; opencode degrades to `provider · $cost`). Live-confirmed.
- [x] **Ghost sessions in `/resume`** — `sessions.recent`/`sessions.count` now skip entries with no
      title (pre-title registry saves). New sessions always get a title (`bot.py`), so this self-heals;
      old ghost entries stay in the registry file but never surface in the picker.

## Up next — sequenced easiest → hardest (2026-07-21)
Ordered so each tier ships value fast without forcing rework in a later tier. Dropped "show full
session id in reply" (Niceties, old) — the `[XXX]` prefix already disambiguates fine, not worth a line.

### Tier 1 — trivial, no deps
- [x] **"bot"-prefix trigger for text** — a message starting with "bot " or "bot," → treat as `/new`
      (new session) instead of INBOX capture. Self-contained routing change in `bot.py`.
- [x] **Native title source — investigated, findings below** — solved. Claude Code (VSCode ext +
      terminal, confirmed both write the same store) appends a `{"type":"ai-title","sessionId":...,
      "aiTitle":"..."}` line to the session's own `~/.claude/projects/<proj>/<sid>.jsonl` — written once
      in the background after an early turn, then re-emitted with the *same* value on later turns (title
      is fixed for the session's life, confirmed by scanning all 103 local transcripts: never saw a
      value change within one file). Read = grep the last `ai-title` line, take `aiTitle`. Zero-cost, no
      LLM call — Claude Code already paid for the generation.
      Gap: ~27/103 transcripts have no `ai-title` line at all (all `entrypoint:"claude-vscode"`, mix of
      very short/aborted sessions and a few unexpectedly long ones — looks like the async title-gen
      sometimes just doesn't fire or the session closed before it landed). The 5 `entrypoint:"cli"` /
      `"sdk-cli"` sessions sampled all had one. Fall back to today's `title_from_prompt` when absent.
      Bonus closed for free: since this reads every `*.jsonl` in the project dir (not just sessions
      aiwbot's own registry remembers), it naturally surfaces CLI-only sessions Lucas starts outside
      aiwbot too (e.g. the ementas one) — no extra plumbing needed.
      opencode: SQLite at `~/.local/share/opencode/opencode.db`, table `session`, column `title` (plain
      TEXT, no parsing) — direct read. Placeholder value `"New session - <ISO timestamp>"` shows before
      a real title is generated; filter that pattern the same way `sessions.py` already filters
      `(SEM TÍTULO)` ghosts.
      Feeds Tier 2's 3-line buttons directly.

### Tier 2 — small, self-contained
- [x] **`/resume` 3-line buttons** — line 1 = title, line 2 = preview (first 6 … last 6 words of that
      session's last agent response), line 3 = time · backend. Preview persisted in the registry
      alongside title, written from the same seam-surfaced text already used for the reply.
- [ ] **Pagination past the top 8 in `/resume`** — today only the 8 most recent sessions show, no
      Next/Prev button; older ones are reachable only via `/resume <termo>` if you remember a title
      word (live search-as-you-type isn't possible in a TG inline keyboard). Add paging.

### Tier 3 — medium, new plumbing but scoped
- [ ] **plan ↔ build mode** toggle, very low-friction (one tap / short command). Claude Code has a
      plan mode; surface an easy switch so a dispatched turn can run in plan vs build.
- [ ] **model + effort selection** — pick the model and the reasoning effort per session/turn (claude:
      medium/high/…; model family), with optimized UX (tap, not typing flags). Sequenced after the plan
      ↔ build toggle since the footer's `effort/mode` slot depends on a real effort signal that doesn't
      exist yet from `claude -p`.

### Tier 4 — large, architecturally heavy — do last, on purpose
Sequenced last specifically so Tier 1-3 UI work (resume picker, buttons) doesn't get rebuilt once the
message-delivery mechanics change underneath it.
- [ ] **Audio support** — transcribe voice notes → dispatch as a turn (today they only land in INBOX
      untranscribed). If the audio starts with "bot", auto-start a NEW session (`/new`). New external
      dependency (STT).
- [ ] **Live feedback** (Phase C, linuz90 mold) — `stream-json`: edit the message as the agent's chat
      text arrives, appending in chunks, keeping "⏳ pensando…" pinned at the END until the turn
      finishes. Builds on the ⏳-morph already shipped. Changes the reply/dispatch mechanics other
      niceties touch — hence last.
- [ ] **Interview / ask_user** (Phase C) — let the bot interview Lucas mid-task (essential for plan
      mode, useful elsewhere): agent questions surface as Telegram prompts/inline buttons, answers flow
      back into the running turn. (linuz90's `ask_user` MCP pattern — see [[reference_linuz90_bot]].)
      Depends on the live-feedback plumbing above.
- [ ] **Phase D — persistent mode + more backends**: claude via SDK `ClaudeSDKClient`, opencode via
      `--attach` server (only if per-message cost annoys); copilot backend; retire/thin the workspace
      bot to INBOX-only capture. Biggest structural rewrite — last on purpose.

## Verification
- Free (every change): `make test`. Live milestone (~$0.20): `make smoke`.
