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
- **VSCode picker needs a window reload** to pick up newly created sessions (the extension caches its
  list). Terminal `claude --resume` re-reads every time. `Ctrl+Shift+P → Reload Window` is the quick way.
- **`resume.RULER_WIDTH = 44`** — eyeball estimate of how wide the monospace ruler must be to
  out-measure a 64-char preview line. Re-tune if the `/resume` bubble ever looks padded or breathes.

## Finish plan — settled 2026-07-26 (supersedes the 2026-07-23 ranking)

Lucas: *"I really want to finish that bot asap, all of it."* The 2026-07-23 lens still holds — each
item scored by *does this remove a reason Lucas has to go back to the PC?* — but the open list is now
sequenced as a **finish line**, not an open-ended backlog.

**Finish line = through `ask_user`.** Once the bot can interview Lucas mid-task it is fully
away-from-PC capable. **show-me** and **Phase D** stay parked past the line: show-me degrades via
artifacts (Lucas 2026-07-23), and Phase D is a structural rewrite that buys cost/latency, not a new
capability.

> **~~F0 bookkeeping~~ → F1 bugs → F2 papercuts → F3 features → F4 streaming → ask_user** ┃ *line* ┃
> ~~show-me~~ · ~~Phase D~~
>
> Next up: **F1 — [b1] tables/bold rendering**.

| Stage | Contents | Why here |
|-------|----------|----------|
| **F0** | stale-checkbox sweep, dedupe contradictions | free, and stops the roadmap lying |
| **F1** | [b1] tables/bold, [b2] opencode error surfacing | bugs taxing *every* reply — best value/hour |
| **F2** | phrase style + emoji, `bote`→`bot`, transcript echo, reply affordance | one branch of papercuts; transcript echo is also the **instrument** for F3b |
| **F3** | NL harness+model parse, audio cadence, button latency | features; F3b needs F2's echo to tune against |
| **F4** | live streaming (`stream-json`) → `ask_user` | heavy, strict order: ask_user needs streaming plumbing |

Earlier P-numbers keep their names so old notes resolve. **P3, P2, panel rounds 2-4 (2026-07-23) and
audio in+out (2026-07-24) all shipped** — see [HISTORY.md](HISTORY.md) and SPECS AD-10…AD-17.

### F0 — bookkeeping ✔ **done 2026-07-26**
- [x] **claude model order `sonnet` `opus` `fable`** — was listed open, but already shipped
      (`claude.py` `_MODELS`, merged `feature/model-order-sonnet-first`). Checkbox was stale.
- [x] **button-latency contradiction resolved** — the same item sat in *both* "known limits (won't
      chase)" and the backlog. Lucas reopened it; the won't-chase entry is gone, the live item is F3.

### F1 — bugs taxing every reply (do first)
Both tracked in [KNOWN-BUGS.md](KNOWN-BUGS.md); a FIXED flip needs a `tests/**/b<N>-*` regression
spec (code/VERIFY.md).
- [ ] **[b1] tables + bold don't render** — every answer passes `markdown.py`/`inline.py`, so broken
      formatting taxes 100% of output. Best value per hour on the whole list. Verify against a real
      captured answer, not a hand-written fixture.
- [ ] **[b2] opencode errors collapse to generic "no text event"** — blocked on capturing a real
      error payload, but fixable *without* one: `_line_to_event` silently drops any line that is not
      `text`/`step_finish`. Surfacing unrecognized lines as an error event makes every *future*
      opencode failure self-diagnosing instead of a mystery — i.e. the fix unblocks its own
      regression fixture. Do the defensive half now; the exact-shape parse when a payload exists.

### F2 — papercut batch (from INBOX 2026-07-24, one branch)
Small, all from Lucas testing the panel live. Ordered by how much each bugs him.
- [ ] **the reply affordance is unclear** — "o bot já aparece toda vez com o campo aberto como se
      minha mensagem fosse um reply, não fica claro sobre o que é o reply". Every anchor is a
      repliable message (reply-to-continue), and Telegram shows the compose box quoting it. Make
      what the reply continues legible — e.g. the anchor's title/`[XXX]` in the quoted preview, or
      a one-line hint. UX, not a bug.
- [ ] **emoji style: minimalist, not "bregas"** — prefer flat glyphs (red circle 🔴 not 🚦-style,
      a plain hourglass over the gradient one) in the ⏳/status phrases. `frontend/phrases.py`.
      Cosmetic, low priority, but batch it with the phrase-style housekeeping item below.
- [ ] **"bot" start-word mis-heard as "bote" by STT** (INBOX 2026-07-24) — the voice/text session-start
      keyword is `bot`, but STT transcribed "bote", so the new-session intent never fired. Two options:
      (a) if the first token of an audio/text is "bote", normalize it to "bot"; or (b) pick a start word
      STT won't corrupt. Pick one. `frontend/` start-word detection.
- [ ] **echo the transcript under Lucas's own voice message** (Lucas, 2026-07-24, WhatsApp does
      this) — right now there's no visible confirmation of what STT heard from *his* audio, only
      the eventual reply. Show the transcript back (e.g. a quoted/quiet reply to his voice message,
      before the turn's real answer) so he can eyeball whether transcription got it right without
      needing to guess from the response. Small — and it is the **instrument** F3b tunes against,
      so it ships before the cadence work, not after.

### F3 — features
- [ ] **NL harness+model selection from the message, zero extra tokens** (INBOX 2026-07-24) — when a
      message starts with "bot, …", parse any mention of a harness (claudecode/opencode/kimicode) and a
      model (opus/sonnet/glm/deepseek/kimi3/kimi2.7) straight from the text to pick backend+model,
      **without** spending a triage inference call. Complements the shipped P2 button panel with a
      language path. `frontend/` dispatch.
- [ ] **audio punctuation + cadence quality is poor** (INBOX 2026-07-24) — both the STT transcript and
      the TTS output need work on punctuation, pauses, and cadence. Refinement on the shipped audio
      lane (`frontend/stt.py` hotwords/params, `frontend/tts.py`). **Needs F2's transcript echo first**
      — without it there is no way to see what STT actually heard, so tuning is blind.
- [ ] **button-tap → response feels slow, not instant** (INBOX 2026-07-26). Investigate the Telegram
      inline-button round trip and cut what is ours. **Reopened by Lucas 2026-07-26** — it had been
      filed under "known limits (won't chase)" on the strength of an earlier "não é crítico", but the
      newer capture says it still bugs him, so the won't-chase entry was deleted rather than left to
      contradict this line. Prior finding stands as the starting point: the optimistic edit already
      removed our latency, leaving `edit_message_reply_markup`'s round trip — so the investigation is
      about whether a local-echo trick exists, not about re-measuring our own path.

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
- Follow-ups moved out of this section: transcript echo → **F2**, punctuation/cadence → **F3**.

### F4 — heavy, strict order; the finish line sits at `ask_user`
- [ ] **Live feedback** (Phase C, linuz90 mold) — `stream-json`: edit the message as the agent's chat
      text arrives, appending in chunks, keeping "⏳ pensando…" pinned at the END until the turn
      finishes. Builds on the ⏳-morph already shipped. Changes the reply/dispatch mechanics other
      niceties touch — hence late.
- [ ] **Interview / ask_user** (Phase C) — let the bot interview Lucas mid-task (essential for plan
      mode, useful elsewhere): agent questions surface as Telegram prompts/inline buttons, answers flow
      back into the running turn. (linuz90's `ask_user` MCP pattern — see [[reference_linuz90_bot]].)
      Depends on the live-feedback plumbing above.

### Past the finish line — parked, not scheduled (Lucas 2026-07-26)
Both survive here because they are real gaps, not because they are queued. Promote one only when a
concrete session's cost makes it worth more than it costs.
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
