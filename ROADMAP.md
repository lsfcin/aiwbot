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

## Up next — sequenced easiest → hardest
Tier 1-2 (bot-prefix trigger, native title source, operate docs, `/resume` preview + pagination) shipped
2026-07-22 — archived in [HISTORY.md](HISTORY.md). Ordered so each tier ships value fast without
forcing rework in a later tier.

### Tier 3 — medium, new plumbing but scoped
plan↔build toggle (sticky, segmented button) + session-parity groundwork shipped 2026-07-22 —
archived in [HISTORY.md](HISTORY.md). Live feedback opened the follow-ups below.

#### Session-parity polish (live feedback 2026-07-22) — do next, cheap → deep
- [x] **claude title = `aiTitle`, not the opening prompt** (2b) — **shipped Phase 1.** New
      `backend/transcript.py` tail-scans the last 64 KB for the latest `ai-title` jsonl event (Claude
      Code's real picker title), `_session_item` prefers it and falls back to `lastPrompt`. Kills
      `[A06] ## RESUME —` labels. (SPECS AD-7)
- [ ] **3-line `/resume` entry redesign** (extra) — each session over 3 lines in the message text
      (buttons stay numeral-only, AD-5): L1 `N. TÍTULO` (6-word cap); L2 `<first 6 words> … <last 6
      words>` of the session's **last response**; L3 `tempo · modo · provider · model · custo · %contexto`.
      The 6…6 preview we agreed on isn't rendering today — wire it in. `frontend/resume.py` `_entry_line`
      + a real preview source (registry `preview` only exists for bot-created turns; VSCode sessions need
      it derived from the jsonl last assistant message). Depends on context-% (below) for L3.
- [x] **bot sessions invisible to VSCode/terminal pickers** (2a) — **SOLVED 2026-07-23.** It was the
      `CLAUDE_CODE_ENTRYPOINT` env var, not the `-p` flag: the backend now sets `claude-vscode` on the
      subprocess, so sessions created by `/new` (explicit or "bot"-prefixed) show up in the native
      picker. Verified live A/B. Applies at session creation — sessions created before this stay
      hidden; the copyable `claude --resume <id>` in the `/resume` anchor covers those. SPECS AD-8.
- [x] **instant mode-button feedback** (1) — the segmented toggle now flips optimistically: answer the
      callback + edit the markup before persisting the mode, so the bracket moves instantly instead of
      after the config write. `frontend/mode.py`. Shipped Phase 1.

#### Shipped 2026-07-23 (live feedback round 2)
- [x] **`/resume` pagination** — 3 per page, `‹ 1 2 3 ›` → `‹ 4 5 6 ›`; numerals stay absolute so a
      button always names the line above it. Arrows carry the active filter in `callback_data`.
- [x] **`/new` usable from the command menu** — tapping it sends `/new` bare, so an empty prompt now
      answers with a `ForceReply` and starts the session from that reply (`pending_new` map).
- [x] **context % + meta reorder + 5-word titles + full last response on re-anchor** — see AD-9.
- [x] **native session visibility** (2a) — `CLAUDE_CODE_ENTRYPOINT`, see AD-8.

#### Known limits (won't chase)
- **Mode-button latency ~1.5 s** — the optimistic edit already removed our side; what's left is the
  Telegram round-trip for `edit_message_reply_markup`. Not fixable without a local-echo mechanism
  Telegram doesn't offer. Lucas: "não é crítico".
- **VSCode picker needs a window reload** to pick up newly created sessions (the extension caches its
  list). Terminal `claude --resume` re-reads every time. `Ctrl+Shift+P → Reload Window` is the quick way.

#### Tier 3 remainder
- [ ] **backend + model + effort selection** (Lucas, 2026-07-23) — three linked pickers, tap-not-type,
      reusing the `TurnOptions` seam (add `backend`/`model`/`effort`; each backend maps what it can):
      1. **switch backend** claude ↔ opencode per session (today only `/new --backend X` at creation).
      2. **switch model** (claude `--model`; opencode has its own catalogue).
      3. **modes conditioned on the backend/model** — build/plan is a Claude Code notion; opencode
         models (e.g. GLM-5.2) likely don't share it. Needs a per-backend capability declaration on the
         seam so the toggle only offers modes the current target actually supports. **Unverified** —
         confirm opencode's real mode/effort surface before designing.
- [ ] **output-format translation** — translate the markdown that Claude Code / opencode emit
      (`**bold**`, `##` headings, code fences) into what Telegram actually renders (MarkdownV2 or HTML).
      Today bold sometimes shows, `##` never does — inconsistent. A translation layer sits between agent
      output and the Telegram send. (INBOX 2026-07-22)
- [ ] **context % in footer** — show the session's context-window usage % alongside `$cost` in each
      message footer. Pairs with the session-size monitor idea (workspace-os TODO:104). (INBOX 2026-07-22)

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
