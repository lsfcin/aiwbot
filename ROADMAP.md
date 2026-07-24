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

## Shipped — archived in [HISTORY.md](HISTORY.md)
Phases A/B, Tiers 1-3, P3, **P2 + P2.1 + panel rounds 3-4** all shipped and live-tested. Design
lives in [SPECS.md](SPECS.md) (AD-1…AD-17); plans in [ROADMAP-p2.md](ROADMAP-p2.md) /
[ROADMAP-p3.md](ROADMAP-p3.md). Details moved out of this file on 2026-07-23.

### Known limits (won't chase)
- **Mode-button latency ~1.5 s** — the optimistic edit already removed our side; what's left is the
  Telegram round-trip for `edit_message_reply_markup`. Not fixable without a local-echo mechanism
  Telegram doesn't offer. Lucas: "não é crítico".
- **VSCode picker needs a window reload** to pick up newly created sessions (the extension caches its
  list). Terminal `claude --resume` re-reads every time. `Ctrl+Shift+P → Reload Window` is the quick way.
- **`resume.RULER_WIDTH = 44`** — eyeball estimate of how wide the monospace ruler must be to
  out-measure a 64-char preview line. Re-tune if the `/resume` bubble ever looks padded or breathes.

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
the running order. **P3, P2, and panel rounds 2-4 all shipped 2026-07-23** — see
[HISTORY.md](HISTORY.md) and SPECS AD-10…AD-17. Next up is **audio**.

### Live feedback — 2026-07-24 (from INBOX, do before or alongside audio)
Small, all from Lucas testing the panel live. Cheap; ordered by how much each bugs him.
- [ ] **claude harness model order → `sonnet` `opus` `fable`** (Lucas, explicit). Currently
      `("opus", "sonnet", "fable")` in `claude.py` `_MODELS`; `test_target` pins the order, flip
      both. One-liner, do first.
- [ ] **the reply affordance is unclear** — "o bot já aparece toda vez com o campo aberto como se
      minha mensagem fosse um reply, não fica claro sobre o que é o reply". Every anchor is a
      repliable message (reply-to-continue), and Telegram shows the compose box quoting it. Make
      what the reply continues legible — e.g. the anchor's title/`[XXX]` in the quoted preview, or
      a one-line hint. UX, not a bug.
- [ ] **emoji style: minimalist, not "bregas"** — prefer flat glyphs (red circle 🔴 not 🚦-style,
      a plain hourglass over the gradient one) in the ⏳/status phrases. `frontend/phrases.py`.
      Cosmetic, low priority, but batch it with the phrase-style housekeeping item below.

### Audio — in **and out** (Lucas, 2026-07-23: "audio wins") ✔ **SHIPPED 2026-07-24**
Beats streaming because it removes a *modality* barrier (hands/eyes busy, walking, driving) rather
than making an existing text exchange prettier. End-to-end: faster-whisper STT (large-v3-turbo,
PT+hotwords) dispatches voice notes into the session graph; Kokoro-82M TTS (pf_dora voice) replies
in OGG/Opus. Reply-continue on voice-to-voice works correctly (fixed transcript-vs-msg.text gap).
- [x] **audio in** — transcribe voice notes → dispatch as a turn (C1, C2, C3); voice note starting 
      with "bot" auto-starts a new session. Empty/exception transcripts degrade safely to 
      untranscribed INBOX + notice (C3). hotwords list explicit editable data (C4).
- [x] **audio out** — bot answers *as* voice note (C5); text-triggered turns unaffected. Both 
      models lazy-loaded; no model load at import time; `make test` green with fake models (C6).
- Shipped (commit hash in HISTORY): STT wrapper `frontend/stt.py`, TTS wrapper + OGG encode 
      `frontend/tts.py`, voice reply `frontend/reply.py`, hotwords data `frontend/hotwords.py`, 
      wiring in `frontend/bot.py`. Contract locked in `frontend/SPEC.md`.

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
