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

> **~~F0~~ → ~~F1~~ → ~~F2~~ → ~~F3~~ → ~~F5 answer shape~~ → F4 streaming → ask_user**
> ┃ *line* ┃ ~~show-me~~ · ~~Phase D~~
>
> Next up: **F4** — the finish line itself, and the only thing left before it. Everything
> else is shipped; b3 closed 2026-07-27 (SPECS AD-24).

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

### Voice + picker fixes ✔ **SHIPPED 2026-07-27** — from Lucas's live test right after F3c
Found by him using the bot, not by a sweep. All four measured against his real chuveiro voice
note rather than reasoned about; specs in AD-21 / AD-22, regression in
`tests/test_voice_echo_and_picker.py`.

- **Punctuation was completely dead** (0.0 marks/100 words), and F3b's stated mechanism was
  wrong: it is not about the prompt's tail, it is that a bare word list *anywhere* suppresses
  punctuation. Jargon dissolved into sentences → **22.5 marks/100 words**.
- **`claude sonnet` → `claudsonner`**, because no model name was primed at all — which also meant
  the F3a spoken directive had been silently dead for anyone saying a model out loud.
- **Transcript echo** is now `<i>"…"</i>` with no `ouvi:` label and no blockquote, echoing the
  *normalized* string that routing acts on (new `startword.normalize`), so it answers the only
  question it exists for: what reached the session.
- **Picker stopped reshuffling itself** on every pick (AD-22).

Still open from the same test: **[b3] context % over 100%** — see [KNOWN-BUGS.md](KNOWN-BUGS.md).
And **submenu latency has no remaining fix**: after F3c a tap is one round trip, measured at
~200 ms Recife→Telegram, and forcing IPv4 was tested and is *slower* than the IPv6 default
(203 vs 191 ms median). Lucas asked whether it could change fast even if the backend lags — it
cannot: a Telegram client draws an inline keyboard only from server state, so there is nothing
local to update optimistically. That round trip is the product's floor, not a bug.

### F5 ✔ **SHIPPED 2026-07-27** — answer-shape papercuts (Lucas, INBOX 2026-07-26)

- **a. Every bubble of a long answer continues the session.** `reply.deliver` now returns *every*
      message it sent instead of just the last, and both callers anchor all of them. Anchoring
      only the tail meant replying to an earlier bubble missed `session_for_reply` and silently
      fell through to INBOX capture — exactly the condition Lucas put on the split UX:
      *"desde que me permitisse, respondendo qualquer uma delas, continuar na mesma sessão"*.
      `msgmap.MAX` went 50 → 400, since one answer now costs as many entries as it has bubbles.
- **b. Long answers split at paragraph boundaries on purpose**, not only when 4096 forces it —
      Lucas's call, asked directly. `split_html` takes an optional soft size
      (`reply.SOFT_CHARS = 900`): past it, the chunk ends at the next blank line, so a bubble
      never stops mid-thought. The hard limit still wins, and a run of blank lines can no longer
      seal an empty chunk. Same path now delivers the `/resume` anchor, which **removes
      `ANCHOR_BODY_MAX`** — that 3000-char mid-word clip, not Telegram's limit, is where the
      `[…]` Lucas reported came from.
- **c. The `continua [5FE] TÍTULO` anchor line is deleted**; the id and title moved to the
      footer (`[ABC] TÍTULO · claude · sonnet · build · $0.031`). This **reverses F2's reply
      anchor** from 2026-07-26 — see AD-23 for why F2's reasoning was sound but aimed at the
      wrong reader. `answer_block` moved out of `format.py` into its own `answer.py` on the way,
      because the change would have pushed `format.py` past the 200-line gate.

Regression: `tests/test_f5_answer_shape.py`.

### F4 — staged plan, settled 2026-07-27

Lucas asked for this one to be planned properly, with checkpoints, because it is the biggest change
in the project. Scratch copy at `~/.claude/plans/sry-for-the-interruption-piped-dewdrop.md`; this is
the canonical home.

**The architectural crux, resolved.** linuz90's `ask_user` works only because it runs the Agent SDK
`query()` **in-process** — its MCP tool handler can await a button press in the same process.
aiwbot is a **subprocess** CLI, the opposite shape, and a stdio MCP server spawned by the CLI would
be a child of the CLI, unable to reach the bot's Telegram state. Resolution, verified against
`claude --help`: the daemon hosts an **HTTP MCP server in-process** and each turn passes
`--mcp-config '<json>' --strict-mcp-config` pointing at `http://127.0.0.1:<port>/mcp/<turn_token>`.
The handler runs *inside the daemon*, so it blocks the agent's turn exactly like the in-process
version — **no Phase D rewrite**, and `opencode mcp` exists so provider-agnosticism holds.

**Measured 2026-07-27, do not re-derive:**
- `--output-format stream-json --verbose` → JSONL `system` / `assistant` (one *completed* message) /
  `rate_limit_event` / `result`. Too coarse alone: a single-message answer shows nothing until the end.
- `+ --include-partial-messages` → `type:"stream_event"` wrapping Anthropic SSE;
  `event.delta = {"type":"text_delta","text":…}`. This is what gives token-level streaming.
- `aiohttp` 3.13.5 installed, `mcp` SDK not — MCP over HTTP is plain JSON-RPC 2.0, **no new dep**.
- **`split_html` is prefix-stable** — property-probed, 43 prefixes, 0 violations. `split_html(prefix)[:-1]`
  is always a prefix of `split_html(full)` when `prefix` ends at a line boundary. This is what makes
  mid-stream bubble sealing *compatible* with AD-23 rather than in conflict with it, and it makes
  AD-23 stronger: bubbles get anchored the moment they are born, so Lucas can reply to bubble 1
  while bubble 3 is still being written.
- `format_body`'s fence regex needs both fences and `inline.convert` only emits balanced tags, so a
  partial render never produces broken HTML — only HTML that may later change.

**Decisions (Lucas):** all stages 0–5 · merge `feature/*` → `develop` after each approved checkpoint ·
`ask_user` waits **1 h** then returns *text* (never an MCP error), pending a probe of the CLI's own
tool timeout · streaming behind `TurnOptions.stream`, default off until Stage 3 passes ·
token-level granularity · a mid-stream error **appends** a bubble, never deletes read text.

| Stage | Goal | Checkpoint |
|---|---|---|
| **0** ✔ | split `bot.py` → `turnrun.py`, zero behaviour change | everything looks exactly as before |
| **1** | streaming seam in the backend, still batch-delivered | log shows frames ticking; Telegram identical |
| **2** | live bubble: throttled painter, `⏳` pinned | text grows ~every 1.5 s, footer+keyboard at the end |
| **3** | seal bubbles mid-stream (full AD-23 under streaming) | reply to bubble 1 *while bubble 2 writes* |
| **4** | `ask_user` MCP transport, probe-gated | question bubble → tap → streamed answer names the choice |
| **5** | `ask_user` in anger, AD-25/AD-26, close F4 | a real plan-mode task, away from the PC |

Key risks pre-empted: 64 KB subprocess stream limit (`limit=1<<20`); stderr pipe fills and hangs the
child (sibling drain task); occupancy read before the transcript flushes would silently regress b3
(`await proc.wait()` before yielding the result event); 429 pile-up (in-flight guard that *drops*
rather than queues, plus self-tuning backoff); `bot.py` 198/200 and `claude.py` 194/200 both split
**before** gaining code.

#### F4 Stage 0 ✔ **SHIPPED 2026-07-27** — `frontend/turnrun.py`
`bot.py` did four things and F4 touches exactly one: running a turn and putting its answer on
screen. That is the cut — chosen by F4's seam rather than by line counting, as this roadmap asked.
It also completes an existing pairing: `turnhelpers.py` is the pure half (*decides*, no I/O),
`turnrun.py` is the impure half (*does*, awaits the backend and Telegram). `bot.py` 198 → 146,
`turnrun.py` 72, and `bot.py` no longer imports `dispatch` at all — asserted by a test, so the two
cannot quietly re-fuse.

### F4 — original sketch (superseded by the staged plan above)
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
- [ ] **`bot.py` is at 198 LOC** (200 is the hard gate) after F3c's startup warm and the voice
      echo change — two lines of headroom left, so the next touch pays for the split. F4 puts
      streaming into exactly this file, so it *will* breach. Split when F4 starts, not now — the
      seam F4 introduces is what should decide where the cut goes.

## Verification
- Free (every change): `make test`. Live milestone (~$0.20): `make smoke`.
