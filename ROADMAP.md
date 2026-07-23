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

> **~~P3~~ → ~~P2~~ → audio (in + out) → live streaming → ask_user → show-me → Phase D**
>
> Next up: **audio (in + out)**.

The P-numbers below keep their original names so earlier notes still resolve; read the arrow above for
the running order.

### ~~P3 — Telegram output fidelity + `/resume` stability~~ — **SHIPPED 2026-07-23**
Live-confirmed by Lucas, 107 tests green. Archived in [HISTORY.md](HISTORY.md); the plan that produced
it stays in [ROADMAP-p3.md](ROADMAP-p3.md). One knob left open on purpose: `resume.RULER_WIDTH = 44`
is an eyeball estimate of how wide the monospace ruler must be to out-measure a 64-char preview line.
Re-tune it if the picker bubble ever looks padded or still breathes.

### P2.1 — panel redesign (Lucas's live feedback, 2026-07-23)
Landed the same day P2 shipped, on Lucas's read of the first cut. Four changes, three of them
corrections rather than additions:

- [x] **The gear became a `+`**, and the panel a positional layout: **at most four buttons per
      row**, first always `+`/`x`, last always `···`/`−`. Went through two iterations the same
      day — the first was a fixed 5-column grid padded with invisible cells so everything was
      square and aligned, which Lucas dropped once he saw the cost: five columns means
      ~8-character labels and model ids stop being distinguishable. Four (or fewer) per row buys
      ~12. Rows split evenly, never 4+1. SPECS AD-13.
- [x] **Harness left the session panel.** Lucas: switching harness mid-session makes no sense
      unless the context moves with it. Checked — it can't, not symmetrically: `opencode` has
      `export`/`import`, `claude` has no counterpart. So a lineage belongs to its harness for life
      and the knob lives only at `/new`. Killed `next_backend`, the switch toast, and the
      new-session-on-switch dispatch path. SPECS AD-11, revised.
- [x] **`provedor` was the wrong word.** Provider = who supplies the key (nvidia, openrouter) —
      opencode's own sense, and the level the drill-down groups by. The CLI above it is the
      **harness**. Buttons are English now (`harness` · `model` · `effort`), matching BUILD/PLAN.
- [x] **`/new` carries the panel.** A bare `/new` answers with a config bubble you adjust and then
      reply to. Telegram allows one `reply_markup` per message, so this costs ForceReply's
      auto-focus — Lucas's call (SPECS AD-14). `/new <prompt>` and the `bot ` prefix are unchanged
      and inherit the last interaction's knobs, which every turn now records as `defaults`.

Round 3 (same day, Lucas testing live):
- [x] **`x` → `‹`, back one level** instead of jumping to the mode row. Paging moved to `«` `»`
      so the two controls stop sharing a glyph in the same column.
- [x] **`effort` is hidden when the model declares none** rather than answering with an alert.
- [x] **The bug behind that alert: systemd could not see `opencode`.** Its PATH is the login
      default and the binary lives in `~/.opencode/bin`, so the catalogue was empty and the
      generic empty-list message fired on the *model* button. Every backend now resolves its
      binary explicitly (`backend/binaries.py`) — which also un-breaks opencode dispatch, which
      would have failed for the same reason. SPECS AD-15.

Found by rendering the real states rather than by reasoning: with only two visible slots, a
collapsed picker would show `low medium ···` while `high` was set — the state invisible. The
selected value is now pinned first whenever the list is truncated, including when it came from
the drill-down and is not in the shortlist at all.

### ~~P2 — backend + model + effort selection~~ — **SHIPPED 2026-07-23**
Plan + measurements: [ROADMAP-p2.md](ROADMAP-p2.md). Design: [SPECS.md](SPECS.md) AD-11 (capability
declaration, backend-switch semantics) and AD-12 (opencode picker parity). 139 tests green.
Live-check pending Lucas.

Delivered: `⚙` on every anchor opens a morphing panel (provedor / modelo / esforço) on the same
message; claude shows its 3 aliases flat, opencode shows a cheap-first shortlist plus a
provider → paged drill-down over 478 models; effort is offered per model and omitted when the model
declares none; switching provider arms a new session on the next turn and clears the
provider-specific knobs. opencode sessions now render the same 3-line `/resume` entry as claude.

Not done as written: **the `frontend/` folder split**. The split that was actually needed happened
along a different seam — `sessions.py` hit the 200-line gate and was cut into `registry.py` (what
the bot remembers) + `sessions.py` (what the providers report), and the keyboard primitives came out
as `keyboard.py`. Grouping the remaining 17 files into `tg/` + `text/` + interaction packages is
still open, but it now buys layout rather than relief; see **Housekeeping**.

The original entry, kept for the reasoning that produced it:

### ~~P2 — backend + model + effort selection (Lucas, 2026-07-23)~~
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
- [x] **switch backend** claude ↔ opencode — shipped as "arm the switch, next turn opens a new
      session on that provider", because a lineage can't change provider (SPECS AD-11).
- [x] **switch model** — shipped as favourites + provider → paged drill-down (Lucas's call over the
      typed escape hatch: tap-not-type held all the way down).
- [x] **effort/mode conditioned on target** — shipped, and the declaration turned out to belong per
      MODEL, not per backend: `models.json` gives four different `reasoning_options` shapes and several
      different `effort` value sets (SPECS AD-11).

- [x] **opencode picker parity** — shipped, see SPECS AD-12 (the `tokens_*` columns turned out to be
      lifetime totals, not occupancy — 175% of the window on a real session).
      Original note: — moved here **from P3 by Lucas's scope call**: claude sessions show a
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
All three closed by P3 — see [HISTORY.md](HISTORY.md). Kept as the record of what the audit found:
long answers could vanish entirely (blind HTML chunking), `/resume N` made one numeral name two
different sessions across pages, and anchor messages carried no mode toggle. Future audits log here
first, then move to KNOWN-BUGS.md with a `bN` id if they survive the round they were found in.

## Housekeeping
- [ ] **PT-BR phrase style: lowercase, no trailing period.** `frontend/phrases.py` was copied from
      the old workspace bot and kept its sentence-case banks ("Guardado em brain/INBOX.md."). A
      parallel session had rewritten exactly these banks in the old daemon to lowercase and
      period-free ("guardado em brain/INBOX.md") — a deliberate tone choice for chat, where
      sentence-case acks read stiff. That edit died with the daemon's retirement 2026-07-23; the
      preference is recorded here so it lands in aiwbot instead. Applies to every bank in
      `phrases.py`, not just the capture acks.
- [~] **`frontend/` file count** — partly addressed by P2, but along a seam this note didn't name.
      What actually hit the 200-line block was `sessions.py`, so the cut was by responsibility
      rather than by layer: `registry.py` (bot-owned per-session state — knobs, titles, message
      maps) vs `sessions.py` (cross-backend listing), plus `keyboard.py` for the inline-keyboard
      primitives both pickers now share and `panelmenu.py` for the panel's states. 17 files, none
      near the gate.
      Still open, and now optional: grouping them into `tg/` (`reply`, `htmlsplit`, `keyboard`),
      `text/` (`format`, `markdown`, `inline`, `phrases`) and an interaction package. That buys
      layout, not relief — and each package costs a facade plus a CONTEXT.md — so it is churn with
      no behaviour change. Worth doing when the audio work or a third picker makes the flat
      directory genuinely hard to read, not before.

## Verification
- Free (every change): `make test`. Live milestone (~$0.20): `make smoke`.
