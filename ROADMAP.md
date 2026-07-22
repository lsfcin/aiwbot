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
- [ ] **claude title = `aiTitle`, not the opening prompt** (2b). `/resume` shows `[A06] ## RESUME —`
      because `_opening_prompt` reads the first `last-prompt` event. Claude Code's real picker title is
      the **`aiTitle`** jsonl event (verified: session `a064881a` carries
      `"aiTitle":"Resume video tool core M4 implementation"`). Fix `backend/claude.py` `_opening_prompt`/
      `_session_item` to prefer the **latest** `aiTitle` (tail-scan the file; it recurs ~24×), fall back
      to `lastPrompt`. Cheap: read last ~64 KB, grep last `aiTitle`.
- [ ] **3-line `/resume` entry redesign** (extra) — each session over 3 lines in the message text
      (buttons stay numeral-only, AD-5): L1 `N. TÍTULO` (6-word cap); L2 `<first 6 words> … <last 6
      words>` of the session's **last response**; L3 `tempo · modo · provider · model · custo · %contexto`.
      The 6…6 preview we agreed on isn't rendering today — wire it in. `frontend/resume.py` `_entry_line`
      + a real preview source (registry `preview` only exists for bot-created turns; VSCode sessions need
      it derived from the jsonl last assistant message). Depends on context-% (below) for L3.
- [ ] **bot sessions invisible to VSCode/terminal pickers** (2a) — `--name` did NOT surface a
      bot-created session ("JUST A TEST") in VSCode `/resume` **or** terminal `claude --resume`; it shows
      only in the bot's own `/resume`. So `-p` sessions are systematically hidden from Claude Code's
      native picker. Investigate the filter (compare a bot `-p` jsonl vs an interactive one for the field
      the picker keys on — `kind`/`entrypoint`/persistence flag; check `--session-id` + no
      `--no-session-persistence`). May be unfixable from outside the closed extension — if so, document
      and drop.
- [ ] **instant mode-button feedback** (1) — the segmented toggle takes ~2 s to reflect a tap (the
      `answer()` + `edit_message_reply_markup` round-trip). Answer the callback immediately / make the
      markup edit optimistic so the bracket flips instantly.

#### Tier 3 remainder
- [ ] **model + effort selection** — pick the model and the reasoning effort per session/turn (claude:
      `--effort {low,medium,high,xhigh,max}`; `--model <family>`), tap-not-type UX. Reuses the
      `TurnOptions` seam (add `model`/`effort` fields; claude maps to flags, opencode maps what it can).
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
