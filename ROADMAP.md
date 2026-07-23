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

## Tiers 1-3 — closed
The old easiest→hardest tier ladder is spent: everything in it shipped except the items now carried in
**Backlog** below, which is re-ranked by value rather than by size. Kept here as the live-feedback log.
Tier 1-2 (bot-prefix trigger, native title source, operate docs, `/resume` preview + pagination) shipped
2026-07-22 — archived in [HISTORY.md](HISTORY.md).

### Tier 3 — medium, new plumbing but scoped
plan↔build toggle (sticky, segmented button) + session-parity groundwork shipped 2026-07-22 —
archived in [HISTORY.md](HISTORY.md). Live feedback opened the follow-ups below.

#### Session-parity polish (live feedback 2026-07-22) — do next, cheap → deep
- [x] **claude title = `aiTitle`, not the opening prompt** (2b) — **shipped Phase 1.** New
      `backend/transcript.py` tail-scans the last 64 KB for the latest `ai-title` jsonl event (Claude
      Code's real picker title), `_session_item` prefers it and falls back to `lastPrompt`. Kills
      `[A06] ## RESUME —` labels. (SPECS AD-7)
- [x] **3-line `/resume` entry redesign** (extra) — **shipped for claude.** `frontend/resume.py`
      `_entry_line` renders L1 `N. TÍTULO` / L2 `<6 words> … <6 words>` of the last response / L3 meta,
      fed by `transcript.last_response_text` via `claude._session_item` (buttons stay numeral-only,
      AD-5). Remaining gap is opencode-only — tracked under **opencode picker parity** below.
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

## Backlog — reprioritized 2026-07-23 (whole-backlog pass)

Ranking lens, chosen deliberately over "easiest first": the bot's job in
[workspace-os](../../brain/goals/workspace-os.md) is **the away-from-PC front door**. So each item is
scored by *does it remove a reason Lucas has to go back to the PC?* — not by size.

**Lucas's call on that ranking (same day):** two overrides. The show-me gap drops to **last** — if the
agent really needs to show something it can publish an artifact, so it never fully blocks. And audio
beats live streaming, with a **new ask: audio *output* too**, not just input. Final order:

> **P3 → P2 → audio (in + out) → live streaming → ask_user → show-me → Phase D**

The P-numbers below keep their original names so earlier notes still resolve; read the arrow above for
the running order.

### P3 — Telegram output fidelity + `/resume` stability ← **IN PROGRESS**
Ships first: cheap, and it touches every single message. Three problems, one root — what the agent
writes is not what Telegram renders. Full plan (design decisions, traps, verification):
**[ROADMAP-p3.md](ROADMAP-p3.md)**.
- [ ] **markdown gaps** — headings, lists, italic, links, blockquote, strike. `markdown.py` already
      does bold/code/fences/tables; agent answers are heading-heavy so `##` leaks into most replies.
- [ ] **HTML-safe delivery** — `reply._chunks` slices already-formatted HTML every 4096 chars blind to
      tags, so a long answer can be **silently dropped entirely**. Tag-aware split + plain-text
      fallback. Ships with the markdown work because more tags = more chances to break.
- [ ] **`/resume` stops jittering** — fixed 5-slot keyboard (inert `‹`/`›` at the ends), character
      budgets instead of word budgets, width ruler, drop the `/resume N` form that corrupts the
      numerals, mode toggle on anchor messages.

### P2 — backend + model + effort selection (Lucas, 2026-07-23)
Three linked pickers, tap-not-type, on the `TurnOptions` seam (gains `backend`/`model`/`effort`; each
backend maps what it can). **The design blocker is gone** — the CLI surfaces were verified live
2026-07-23 and every knob maps on both sides:

| knob | claude | opencode |
|------|--------|----------|
| mode | `--permission-mode plan\|bypassPermissions` (wired) | `--agent plan\|build` — **both are primary agents; the earlier "opencode has no plan/build" claim was wrong** |
| model | `--model` (alias `opus`/`sonnet`/`fable`, or full id) | `-m provider/model`, catalogue from `opencode models` (**478** entries) |
| effort | `--effort low\|medium\|high\|xhigh\|max` | `--variant` (provider-specific, e.g. `minimal\|high\|max`) |

Second reason this ranks high: it is a **money lever, not a nicety**. A claude turn costs ~$0.11 even
when trivial; routing a throwaway phone question to a free opencode model is a per-message saving Lucas
can make with one tap.
- [ ] **switch backend** claude ↔ opencode inside an existing session (today only `/new --backend X`).
- [ ] **switch model** — a 478-entry catalogue can't be a flat keyboard: needs provider → model drill-down,
      or a short curated favourites list plus a typed escape hatch.
- [ ] **effort/mode conditioned on target** — still wants a per-backend **capability declaration** on the
      seam (the toggle offers only what the current target supports), but now as a mapping table, not an
      open question. `frontend/mode.py`'s segmented button is the UX mould for all three.

- [ ] **opencode picker parity** — moved here **from P3 by Lucas's scope call**: claude sessions show a
      3-line entry with last-response preview, model, and context %; opencode sessions show none of it,
      because `opencode._row_to_item` returns only `{session_id, title, updated_at}`. It only starts
      mattering once opencode is genuinely in rotation, which is what P2 causes. **Proven cheap while
      exploring 2026-07-23** (no design work left, just do it): opencode's sqlite `message.data` carries
      `modelID`, `providerID`, `tokens.total` and `mode`/`agent`; `part.data` type=`text` carries the
      response text; `~/.cache/opencode/models.json` gives `limit.context` per model, which is the
      window the context % needs. Same read-only sqlite pattern already in `opencode.list_sessions`.

### Audio — in **and out** (Lucas, 2026-07-23: "audio wins")
Promoted above live streaming. Beats streaming because it removes a *modality* barrier (hands/eyes
busy, walking, driving) rather than making an existing text exchange prettier.
- [ ] **audio in** — transcribe voice notes → dispatch as a turn (today they land in INBOX
      untranscribed, `bot.py` `_handle_message`). A voice note starting with "bot" auto-starts a new
      session, mirroring the existing text prefix trigger.
- [ ] **audio out** (new ask) — the bot answers *as* a voice note, so a turn can be consumed without
      looking at the screen. Telegram `send_voice` wants OGG/opus, which is what local TTS emits.
      Both halves need a local model (STT + TTS) — the one item in the backlog carrying a new external
      dependency. Note the INBOX entry about a light TTS model, and check PT-BR support before
      choosing: a bot that answers in English-accented Portuguese is worse than text.

### Later — architecturally heavy
- [ ] **Live feedback** (Phase C, linuz90 mold) — `stream-json`: edit the message as the agent's chat
      text arrives, appending in chunks, keeping "⏳ pensando…" pinned at the END until the turn
      finishes. Builds on the ⏳-morph already shipped. Changes the reply/dispatch mechanics other
      niceties touch — hence late.
- [ ] **Interview / ask_user** (Phase C) — let the bot interview Lucas mid-task (essential for plan
      mode, useful elsewhere): agent questions surface as Telegram prompts/inline buttons, answers flow
      back into the running turn. (linuz90's `ask_user` MCP pattern — see [[reference_linuz90_bot]].)
      Depends on the live-feedback plumbing above.
- [ ] **show-me: outbound media + channel awareness** (from INBOX 2026-07-22) — **demoted to last by
      Lucas 2026-07-23**: "if the model needs it, it can build an artifact anyway", so the gap degrades
      instead of blocking. Kept on the list because the degraded path costs a round trip every time.
      Two halves: (1) **outbound** — the agent emits a file path or artifact URL and the bot ships the
      actual file/preview into the chat (`send_photo`/`send_document`), needing a sentinel convention
      the frontend strips plus size/type guards; (2) **channel awareness** — the turn knows whether it
      arrived from Telegram or VSCode, so the agent picks *how* to check with Lucas (send the image vs.
      "look at your screen"). Injectable per-turn on `TurnOptions`, same as mode. Lucas's words:
      *"garantir que o modelo tem como me mostrar NO telegram o que ele precisar, enviar pdfs, links,
      talvez focar em artifacts seja mais fácil… garantir essa parte de 'checar' … remotamente"*.
- [ ] **Phase D — persistent mode + more backends**: claude via SDK `ClaudeSDKClient`, opencode via
      `--attach` server (only if per-message cost annoys); copilot backend; retire/thin the workspace
      bot to INBOX-only capture. Biggest structural rewrite — last on purpose.

## Usability bugs found in the live bot (audit 2026-07-23)
Logged here rather than KNOWN-BUGS.md because each is being fixed inside a backlog item above, not
independently. Anything left unfixed at the end of P3 moves to KNOWN-BUGS.md with a `bN` id.
- **Long answers can vanish entirely** — `reply._chunks` splits formatted HTML blind to tags; an
  invalid chunk is rejected by Telegram, retried once, then dropped to stderr. → P3.
- **`/resume N` corrupts the numerals** — `cmd_resume` honours a count, `_turn_page` hardcodes 3, so
  one numeral names two different sessions across pages (breaks AD-5's guarantee). → P3.
- **Anchor messages carry no mode toggle** — every answer shows BUILD/PLAN, the `/resume` anchor you
  reply to doesn't, so on re-anchor you can't see the mode you're about to run in. → P3.

## Verification
- Free (every change): `make test`. Live milestone (~$0.20): `make smoke`.
