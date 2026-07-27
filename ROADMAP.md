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
Phases A/B, Tiers 1-3, P3, **P2 + P2.1 + panel rounds 3-4**, **audio in+out**, and the finish
plan's **F0–F2 + F3a + F3b** all shipped and live-tested. Design lives in [SPECS.md](SPECS.md)
(AD-1…AD-17); plans in [ROADMAP-p2.md](ROADMAP-p2.md) / [ROADMAP-p3.md](ROADMAP-p3.md).

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

> **~~F0 bookkeeping~~ → ~~F1 bugs~~ → ~~F2 papercuts~~ → ~~F3 features~~ → F5 papercuts 2 → F4 streaming → ask_user**
> ┃ *line* ┃ ~~show-me~~ · ~~Phase D~~
>
> Next up: **F5** (Lucas's 2026-07-26 capture — three answer-shape papercuts), then **F4**.
> F5 lands before F4 on purpose: it changes what an answer message *looks like*, and F4 rewrites
> how an answer is *delivered*. Doing the cheap shape change on the stable delivery path costs
> less than redoing it on top of streaming.

| Stage | Contents | Why here |
|-------|----------|----------|
| **F0** | stale-checkbox sweep, dedupe contradictions | free, and stops the roadmap lying |
| **F1** | [b1] tables/bold, [b2] opencode error surfacing | bugs taxing *every* reply — best value/hour |
| **F2** | phrase style + emoji, `bote`→`bot`, transcript echo, reply affordance | one branch of papercuts; transcript echo is also the **instrument** for F3b |
| **F3** | NL harness+model parse, audio cadence, button latency | features; F3b needs F2's echo to tune against |
| **F4** | live streaming (`stream-json`) → `ask_user` | heavy, strict order: ask_user needs streaming plumbing |

Earlier P-numbers keep their names so old notes resolve. **P3, P2, panel rounds 2-4 (2026-07-23) and
audio in+out (2026-07-24) all shipped** — see [HISTORY.md](HISTORY.md) and SPECS AD-10…AD-17.

### F0–F2, F3a, F3b ✔ **SHIPPED 2026-07-26** — archived in [HISTORY.md](HISTORY.md)
Bookkeeping, both F1 bugs (b1 tables/bold, b2 opencode errors), the F2 papercut batch (phrase
tone, flat glyphs, reply anchor, transcript echo, `bote`→`bot`), F3a inline harness/model
selection, and F3b token-free punctuation/cadence + hallucination guard. 6 commits, 239 tests
green, all live-confirmed after the daemon restart. Method throughout: decide on measured data
(4000 answers, 412 tables, Lucas's 15 voice notes, live prototypes), not hunches.

### F3c ✔ **SHIPPED 2026-07-27** — button-tap latency, measured then cut

The prior finding ("the optimistic edit already removed our latency") was **half right, and the
half it got wrong was the whole complaint**. Measured rather than reasoned about — benchmark of
every callback path against a copy of the live config, plus RTT to `api.telegram.org` from
Lucas's machine:

| | measured |
|---|---|
| bot-side work, warm, worst path (`menu_dims` on opencode) | **0.8 ms** |
| `api.telegram.org` RTT, pooled connection | **222 ms** median (175 min / 287 max) |
| `catalog.model_ids()` — `opencode models` subprocess | **839 ms**, once per process |

So our compute never mattered — it is ~0.3% of one round trip. Three real costs, all fixed:

1. **Two sequential round trips per tap.** `answerCallbackQuery` (clears the button spinner) and
   `editMessageReplyMarkup` (moves the bracket) were awaited one after the other: ~445 ms. They
   are independent calls on different objects, so `panel._redraw` now `asyncio.gather`s them —
   **~445 ms → ~222 ms**.
2. **Three round trips on the commonest tap.** Picking a model/effort value answered *twice* —
   once in `_choose`, then again in the `_open` it routed into (~667 ms). `_route` now takes the
   toast as an argument so every branch ends in exactly one `_redraw`. **~667 ms → ~222 ms.**
3. **A ~865 ms stall on the first tap after every daemon restart.** `opencode models` (839 ms) +
   the 3 MB `models.json` parse (26 ms) are memoized for the process's life, but the first
   model/menu tap paid them *before* answering. New `choices.warm()`, awaited in `_post_init`
   off the event loop, moves that to startup. Asked through the backend seam, so a third backend
   is warmed by existing.

**The floor is one round trip (~222 ms) and no trick beats it.** That answers the question this
item was actually posed as: a Telegram client renders an inline keyboard purely from server
state — there is no client-side optimistic update, no local echo. The only instant feedback that
exists is the button's built-in spinner, which is already what `answerCallbackQuery` clears.
`concurrent_updates(True)` was **considered and rejected**: it lets back-to-back taps overlap but
does nothing for the latency of a single tap (the complaint), while widening the race window on
`config.json`'s non-atomic read-modify-write.

Regression spec: `tests/test_f3c_tap_latency.py` — asserts the *count* of round trips per tap
(one answer, one redraw, started concurrently), which is the only part we control.

### F5 — answer-shape papercuts (Lucas, INBOX 2026-07-26; scoped 2026-07-27)
All three are about what one answer message looks like. Cheap, and worth doing before F4 rewrites
delivery.

- [ ] **a. Every chunk of a long answer must continue the session.** `reply.deliver` already
      splits at Telegram's 4096 (`split_html`), but `bot._run_and_deliver` maps only the LAST
      chunk's `message_id` to the session — so replying to any earlier bubble misses
      `session_for_reply` and silently falls through to INBOX capture instead of continuing the
      turn. Lucas's own condition on the split UX: *"desde que me permitisse, como usuário,
      respondendo qualquer uma delas, continuar na mesma sessão"*. Fix: `remember_reply` for
      every sent chunk, not just the tail.
- [ ] **b. Split long answers into several messages on purpose.** Lucas, asked directly
      (2026-07-27), chose **always split at paragraph boundaries**, not only when 4096 forces it:
      *"talvez fosse até uma estratégia de UX partir a resposta em várias mensagens pra parecer
      mais como uma conversação"*. Needs a target size (start ~800–1200 chars, tune by eye) and a
      paragraph-boundary rule in `htmlsplit` alongside the existing hard limit. Depends on (a) —
      shipping (b) without it multiplies the dead-reply bug by the number of bubbles.
- [ ] **c. Drop the `continua [5FE] TÍTULO` anchor line; move the title to the footer.**
      *"acho que pode desaparecer, quando o bot responde a mim, como já mostra que é uma resposta"*
      and *"o título pode ficar no rodapé, fica melhor"*. This **reverses the F2 reply anchor**
      shipped 2026-07-26 — F2's reasoning (Telegram quotes a message from its start, so the
      session name had to lead) is sound but was solving for the wrong reader: the bot's answer
      is already `do_quote`d onto Lucas's own message, so the thread is visible without it.
      Touches `format.answer_block` / `_anchor_line` and `tests/test_f2_papercuts.py`. Delete the
      anchor line outright rather than demoting it, and record the reversal in SPECS.

Also found while measuring F3c, not from the INBOX — the `[…]` Lucas saw was **not** Telegram's
limit, it was ours: `resume.ANCHOR_BODY_MAX = 3000` hard-clips the `/resume` anchor's
last-response body mid-word. Fold into (b): the anchor should split like an answer does instead
of carrying its own arbitrary cap.

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
- [ ] **`bot.py` is at 195 LOC** (200 is the hard gate) after F3c added the startup warm. F4 puts
      streaming into exactly this file, so it *will* breach. Split when F4 starts, not now — the
      seam F4 introduces is what should decide where the cut goes.

## Verification
- Free (every change): `make test`. Live milestone (~$0.20): `make smoke`.
