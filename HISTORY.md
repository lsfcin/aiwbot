## Completed — 2026-07-27

Method throughout: every decision measured, not reasoned about. Three separate times the
measurement overturned the stated theory — F3c's "our latency is already gone", F3b's
"punctuation comes from the prompt's tail", and b3's assumption that the context window was the
suspect. That is the session's real lesson: a plausible mechanism written in a spec is not
evidence, and the cost of checking was minutes each time.

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


#### F4 Stage 0 ✔ **SHIPPED 2026-07-27** — `frontend/turnrun.py`
`bot.py` did four things and F4 touches exactly one: running a turn and putting its answer on
screen. That is the cut — chosen by F4's seam rather than by line counting, as this roadmap asked.
It also completes an existing pairing: `turnhelpers.py` is the pure half (*decides*, no I/O),
`turnrun.py` is the impure half (*does*, awaits the backend and Telegram). `bot.py` 198 → 146,
`turnrun.py` 72, and `bot.py` no longer imports `dispatch` at all — asserted by a test, so the two
cannot quietly re-fuse.


### F4 Stages 1–3 ✔ **SHIPPED 2026-07-27** — live streaming
Staged plan and its measured facts stay in [ROADMAP.md](ROADMAP.md) § F4 (Stages 4–5 still open).

- **Stage 1 — the streaming seam.** `proc.communicate()` blocked until the CLI exited, so no line
  could reach Python before the turn was over. New `proc.stream_lines` yields each stdout line as
  it lands, then one terminal tuple *after* the process exits — that ordering is load-bearing,
  because occupancy is read from the provider's store and the store is only written on exit, so
  emitting the result event earlier silently reintroduces b3. Two traps built in from the start,
  both of which only ever appear live on long turns: the asyncio reader's 64 KB line limit raised
  to 1 MB, and stderr drained by a sibling task (a child whose stderr pipe fills blocks forever).
  `AgentEvent.partial` distinguishes deltas (concatenate) from whole segments (join with `\n`),
  defaulting to `False` so every existing fixture stayed correct untouched. `claude.py` 194 → 142
  by moving parsing to `claudeparse.py` **before** it gained flags. Verified live: first text
  1.54 s before process exit, `ctx=31067/1000000` proving occupancy still read correctly.
- **Stage 2 — the live bubble.** `answer.frames()` renders settled markdown and appends the still
  arriving tail as escaped plain text; `markdown.stable_prefix` defines "settled" as everything up
  to the last blank line *outside an open code fence* — a parity count, not a regex, because
  inside a fence a blank line is code, not a paragraph break. `block()` delegates to `frames()`,
  so the finished answer and a streamed frame are one code path, which is what makes the AD-23
  non-regression meaningful rather than two implementations that happen to agree. The throttle is
  a clock gate inside `paint()`, not a background ticker, so nothing races the end of the turn; a
  paint already in flight is **dropped, not queued**, which is lossless because every frame
  recomputes from the whole text.
- **Stage 3 — sealing.** `split_html` is prefix-stable: a single forward pass whose seams depend
  only on lines already consumed, so appending can change nothing but the last chunk. Property
  test written *first*, over 25 corpora × every line-boundary prefix: **0 violations**. Bubbles
  are therefore sent the moment they appear and never touched again, and anchored on arrival —
  making AD-23 *continuous* and strictly stronger than before, since a reply to bubble 1 works
  while bubble 3 is still being written. `painter.finish()` writes only the live bubble onward,
  because re-delivering sealed ones would post the answer twice.

### Tuning and operational fixes (2026-07-27)
- **The daemon's stdout was block-buffered.** The journal is a pipe, so every `print()` sat in an
  8 KB buffer until the process exited — meaning *every* diagnostic in the bot had been invisible
  while it ran, error paths included, and only surfaced in a burst at shutdown. Found because a
  streaming log line Lucas was told to grep for never appeared; restarting flushed the buffer and
  proved the turn had streamed correctly all along. Fixed with `PYTHONUNBUFFERED=1` in the
  systemd unit, documented in README.
- Repaint cadence tuned by Lucas against real turns: 1.5 s → 5 s → **3 s**. The test pins the
  *spacing* invariant against the constant rather than a literal, so tuning never edits a test.
- Native `ChatAction.TYPING`, re-lit every 4 s, fired on the **first** delta independently of the
  repaint gate — so the wait before the first visible words is never silent.
- Pin lost its `·` and gained a blank line of distance; footer title 3 → 5 words, with
  `title_words` gaining a `limit` separate from `n` because the `/resume` picker budgets for
  bubble *width* while a footer line does not.

### Assessed and rejected (2026-07-27)
- **Telegram's new rich text editor** — the blog announces headings and tables, and Lucas's
  screenshots confirm the composer offers both. But Bot API 10.0's entity list has no `HEADING`
  and no `TABLE`: it is a **client-side composer**, not new bot surface. So AD-18's
  pipe-tables-as-row-blocks stands as correct rather than as a workaround. Left instrumented
  rather than merely argued: `bot.py` logs incoming entity types, so one message written with a
  heading and a table settles it by measurement.
- **`concurrent_updates(True)`** — overlaps separate taps but does nothing for a single tap's
  latency (the actual complaint), while widening the race on `config.json`'s non-atomic write.
- **Forcing IPv4 to Telegram** — measured *slower* than the IPv6 default (203 vs 191 ms median).

## Resolved Bugs — 2026-07-27

- **[b3] context occupancy reported impossible percentages** (over 100%, sometimes over 200%).
  The denominator was innocent — the learned windows were a correct 1,000,000. The numerator was
  a **sum over every API request in the turn**: a turn using tools makes several requests and each
  re-reads the whole context from cache, so `modelUsage`'s token fields measure *spend*, not how
  full the window is. Real transcripts summed to 5921%, 6507%, 32533%. The insidious part, and
  why it earned a spec (AD-24) rather than a patch: the wrong number was **not always visibly
  wrong** — one session summed to a perfectly plausible 62% when the truth was 5%. Fixed with a
  `CliBackend.occupancy()` seam reading each provider's own per-message store (claude: the
  transcript's last assistant message; opencode: `ocstore.last_turn`, which also gave opencode a
  context percentage for the first time). `ocstore.py` had already documented this exact trap for
  opencode's accumulating `tokens_*` columns and the claude path walked into it anyway — which is
  why the rule now lives on the seam instead of in one backend's memory. Regression:
  `tests/test_b3_context_pct.py`.

# aiwbot — History
> Archive of completed work. Open work lives in [ROADMAP.md](ROADMAP.md).

## Completed — 2026-07-26 (finish plan F0–F3, all live-confirmed)

The open backlog was sequenced as a **finish line** (F0 bookkeeping → F1 bugs → F2 papercuts →
F3 features → F4 streaming → `ask_user`); F0 through F3 shipped this session, 6 commits on
`feature/finish-plan`, 239 tests green (from 186). show-me and Phase D parked past the line.
A method ran through all of it: **decide on measured data, not hunches** — 4000 real answers for
F1, 412 real tables for the table rewrite, Lucas's own 15 voice notes for F3b, live Telegram
prototypes for every F2 UX call.

**F0 — bookkeeping.** Two roadmap lies removed: the claude model order (`sonnet, opus, fable`)
was listed open but had already shipped; button latency sat in *both* "won't chase" and the
backlog, so on Lucas reopening it the won't-chase entry was deleted and it moved to F3.

**F1 — bugs taxing every reply** (both in Resolved Bugs below). b1 tables/bold and b2 opencode
error surfacing, each closed with a `tests/**/b<N>-*` regression spec built from a real payload.

**F2 — papercut batch** (`tests/test_f2_papercuts.py`). Every choice made by Lucas against a
live prototype sent through the real pipeline: phrase banks → lowercase, period-free, tone rule
now a comment at the head of `phrases.py`; `⏳` → flat `·`; the reply anchor (`answer_block`) now
*leads* with `continua [ABC] TÍTULO` because Telegram quotes a message from its start, so the
footer label was invisible in the compose preview; `bote`→`bot` STT mishearing normalized, with
start-word detection extracted to `frontend/startword.py`; STT transcript echoed back quoted
under Lucas's own voice note (also the instrument F3b tuned against).

**F3a — inline harness/model selection, zero tokens** (`frontend/directives.py`,
`tests/test_directives.py`). `bot, opencode glm resume o pdf` reads its harness/model off the
leading words by matching what the backends already declare — no triage inference. Harness via a
data alias table, model by normalized match (`glm`→`nvidia/z-ai/glm-5.2`), a model implying its
harness. Reads only the leading run so mid-prose mentions are safe; a task-less message is left
untouched. Applied via `turnhelpers.apply_directives`, reusing `panel.apply` so the
harness-clears-model rule stays in one place. Voice turns get it free (same bot-prefix branch).

**F3b — punctuation + cadence, token-free** (`frontend/speech.py`, `tests/test_speech.py`,
`tests/test_stt.py`; contract in `frontend/SPEC.md`). Three findings on Lucas's own voice notes:
(1) Whisper punctuates when its `initial_prompt` is punctuated — free; (2) `initial_prompt` and
`hotwords=` share one conditioning slot, so the jargon now rides *inside* a punctuated carrier
(`hotwords.CARRIER`) rather than losing to it (which had turned "bote" into "Pode"); (3) most bad
cadence was not the TTS model — the voice reply was fed `format.plain` (= `html.escape`), so
Kokoro was pronouncing `&#x27;`, `##`, `**` and table pipes; `speech.to_speech` renders prose
instead. Plus a **hallucination guard** found along the way: Whisper invents words on near-silent
audio and no decoding setting stops it (VAD only shortened `e-mail e-mail` to `e-mail.com`), so
the guard is the model's own confidence — real transcripts scored -0.15..-0.48, garbage -1.49, so
`_MIN_LOGPROB = -0.9` splits them and a rejected transcript rides the C3 fail-safe.

### Audio — in **and out** (shipped 2026-07-24, archived here)
End-to-end voice: faster-whisper STT (large-v3-turbo, PT) dispatches voice notes into the session
graph; a voice note opening with "bot" starts a new session; Kokoro-82M TTS (pf_dora) replies in
OGG/Opus; empty/exception transcripts degrade to untranscribed INBOX + notice (C3); models
lazy-loaded so `make test` stays import-safe with the deps absent (C6). Wrappers `frontend/stt.py`
/ `frontend/tts.py`, voice reply `frontend/reply.py`, hotwords data `frontend/hotwords.py`.
Contract in `frontend/SPEC.md`. (F3b later reworked the STT conditioning and TTS input feeding.)

### Housekeeping done
- **PT-BR phrase style** (lowercase, period-free) — carried over from the retired daemon's
  preference and applied to every bank in `phrases.py` as part of F2.

## Resolved Bugs — 2026-07-26

- **[b1] tables and bold don't render** — the original hunch (escaping order / pipe-table
  detector) was wrong; escaping was correct throughout. Probing 4000 real assistant answers found
  **two independent causes**: (1) `<pre>`-boxed tables escaped their own contents, freezing cell
  markdown into literal `**` — and 0 of 412 real tables fit a phone-width bubble anyway (median
  widest row 151 chars), so `<pre>` boxing is gone, replaced by `frontend/table.py` rendering rows
  as labelled blocks; (2) `_BOLD_RE`'s non-greedy close took 2 of 3 trailing asterisks in
  `**bold *italic***`, emitting `<b>x <i>y</b></i>` — Telegram rejects crossed entities and
  `reply._send_plain` then strips *every* tag, so one run cost a whole message its formatting;
  fixed with a `(?!\*)` lookahead. Spec `tests/test_b1_table_bold.py`; the 4000-answer probe now
  reports 0 rejections.
- **[b2] opencode errors collapse to generic "no text event"** — the prior analysis was right,
  only the payload shape was missing. Earlier repros hung because they *resumed* a session;
  forcing the error on a *fresh* run (`-m <bogus model>`) returns instantly with
  `{"type":"error",…,"error":{"name":"UnknownError","data":{"message":…}}}` and **exit code 0**,
  which is why `proc.py` never treated it as a hard fail. `_line_to_event` now maps `type=="error"`
  (preferring `error.data.message` — opencode labels everything `UnknownError`), and
  `events_from_run` treats a zero-event parse as a failure that quotes the raw tail, so the next
  unrecognized shape names itself. Spec `tests/test_b2_opencode_error.py` +
  `tests/fixtures/opencode_error.jsonl`.

## Completed — 2026-07-23

### Backlog re-ranked by away-from-PC value
The easiest→hardest tier ladder was retired. Every item re-scored against one question — *does this
remove a reason Lucas has to go back to the PC?* Two of the open items turned out to be already
shipped (3-line `/resume` entries, context % in the footer) and the item that most often forces a trip
to the desk wasn't on the list at all. Lucas then overrode two calls: outbound media dropped to last
("if the model needs it it can build an artifact anyway") and audio was promoted above live streaming
with a new ask for audio **output**. Running order settled as P3 → P2 → audio → live streaming →
ask_user → show-me → Phase D.

**AD-10** recorded the verified CLI surfaces that had been blocking the P2 design: opencode does have
plan/build (`--agent`, both primary), a `--variant` effort knob, and 478 models; claude has `--effort
low..max` and `--model`. The earlier "opencode has no plan/build equivalent" claim was wrong, in both
the roadmap and `opencode.build_args`'s docstring.

### P3 — Telegram output fidelity + `/resume` stability
Plan: [ROADMAP-p3.md](ROADMAP-p3.md). Live-confirmed by Lucas, 107 free tests green (from 80).

- **Markdown gaps closed.** Headings (`#`/`##` → bold caps, `###`+ → plain bold), bullets with one
  nest level, numbered lists, blockquote, links, italic, strikethrough, horizontal rule. Inline
  conversion split into `frontend/inline.py`; it now stashes code spans *before* any other rule runs,
  so markdown inside backticks reaches Telegram untouched — a latent bug in the old converter. The
  rule renders as `─────`, deliberately not `· · ·`, which already means "answer ends here" in every
  footer. Unsafe link schemes stay as plain text.
- **Long answers stopped vanishing.** `reply._chunks` had been slicing already-formatted HTML every
  4096 chars blind to tags: a cut inside `<b>` or `<pre>` produced markup Telegram rejects, retried
  once, then dropped to stderr with nothing reaching the phone. New `frontend/htmlsplit.py` splits on
  line boundaries carrying an open-tag stack across the seam (hrefs intact), and `safe_reply` gained a
  last resort — on a parse error, resend once with tags stripped. A degraded message beats a silent
  drop.
- **`/resume` stopped resizing.** Two causes, both fixed: the keyboard swung between 4 and 5 buttons
  at the ends of the range (arrows now hold their slot and go inert there, `noop:`), and the text was
  budgeted in *words*, which is not the unit width is measured in — a 5-word title runs 15-60 chars.
  Titles cap at 32 chars, previews at 64, and a monospace NBSP ruler pins a minimum width
  (`RULER_WIDTH`, eyeball-tuned, 0 disables). Line widths went from up to 140 chars down to a 25-65
  band.
- **Two usability bugs fixed alongside**: `/resume N` set a page size `_turn_page` ignored, so page 1
  showed 1-5 and page 2 showed 4-6 — one numeral naming two sessions, the one thing AD-5 exists to
  prevent (the numeric form is gone; a bare number is now a filter term). And the `/resume` anchor
  finally carries the BUILD/PLAN toggle every answer already had.

## Completed — 2026-07-22

### Tier 1 — bot-prefix trigger, native title source, operate docs
- **"bot"-prefix trigger**: text starting "bot " / "bot," routes to `/new` instead of INBOX capture
  (`bot.py::_strip_bot_prefix`).
- **Native title source investigated**: Claude Code writes a `{"type":"ai-title","aiTitle":...}` line
  into the session's own `~/.claude/projects/<proj>/<sid>.jsonl` — fixed for the session's life once
  written, zero-cost read (no LLM call). ~27/103 local transcripts lack it (mostly short/aborted
  sessions). opencode exposes an equivalent `session.title` column directly in its sqlite db
  (`~/.local/share/opencode/opencode.db`), placeholder value `"New session - <ts>"` before a real
  title lands. Findings fed directly into the Tier 2 picker below.
- **Operate docs**: README.md now documents systemd start/stop/restart/logs commands, the
  restart-after-code-change gotcha (service reads straight off the working tree), and the
  no-linger-yet reboot caveat.

### Tier 2 — `/resume` picker with preview + simplified pagination
- Preview (first 6 … last 6 words of the session's last agent response) added to `/resume`, persisted
  in the registry alongside title (`format.response_preview`, `sessions.remember`).
- **Redesigned after a live test**: the original plan (3-line inline buttons) doesn't work — Telegram
  inline buttons don't render multi-line labels, confirmed live (text collapsed into one truncated
  line; see SPECS.md AD-5). Shipped instead: a numbered list with preview in the message *text*
  (`resume._list_text`/`_entry_line`), numeral-only buttons in a single row, order-matched to the list.
- Pagination simplified: default shown count 5 (was 8, felt like too many); `/resume <n>` overrides the
  count directly (e.g. `/resume 15`) instead of a Next/Prev pager; header hints the override when more
  sessions exist than shown.
- Gitflow: `feature/roadmap-tier1`, `feature/resume-3line-buttons`, `feature/resume-list-and-count`,
  `feature/resume-numeral-buttons` (+ small routing-sync branches) → `develop` → `main`, all pushed.

## Completed — 2026-07-21

### Phase B — Telegram frontend on the seam (live-confirmed)
- `frontend/` on the AgentBackend seam: `/new [--backend claude|opencode]`, reply-to-continue,
  plain text/media → brain/INBOX.md capture, `/help`. Own config dir `~/.config/aiwbot/`, own bot
  handle @lsfaiwbot. Reuses old-bot plumbing (config shape, md→TG-HTML formatting, phrase banks).
- New `frontend/sessions.py` registry tracks session_id→backend locally — there's no cross-backend
  `claude agents --json` equivalent, so the frontend must remember which backend owns each session.
- Scope trimmed vs the old bot: `/select`/`/notify` deferred (need cross-backend session listing),
  `/stop`/`/status` dropped (obsolete — `send()` is one subprocess call per turn, no `--bg` pid).
- **Single-lineage fix**: dropped claude's `--fork-session` → plain `--resume`. The fork (stale AD-3,
  from the old `--bg` era) was minting a new session id per turn and piling up cumulative VSCode
  session entries. Plain resume keeps one id / one transcript / one VSCode entry that grows in place
  — verified live (3 chained turns, same id, context kept). Matches linuz90's SDK design
  ([[reference_linuz90_bot]]). Graceful "session live elsewhere in VSCode" message for the
  concurrent-edit edge.
- **⏳-morph UX**: the "trabalhando…" placeholder is edited in place into the final answer (feels
  like a substitution), not left as a separate message. Seed of Phase C streaming.
- Verify: 16 free tests green (`make test`). Live-confirmed by Lucas via @lsfaiwbot (single lineage,
  full conversations visible in VSCode). Gitflow: `feature/telegram-frontend` → merged to `develop`.

### Phase A — prove the provider-agnostic seam
- `AgentBackend`/`AgentEvent` seam + `CliBackend` driver + `check_contract` (backend/base.py, cli.py).
- `claude` + `opencode` backends: `build_args` + pure `parse_events` (backend/claude.py, opencode.py).
- Free fixture unit tests — 6 green (`make test`, tests/).
- Live smoke (`make smoke`): both backends pass end-to-end + single-lineage resume. **Risk retired** —
  the one interface holds across a forking backend (claude, `--fork-session`, new id/turn) and a
  same-lineage backend (opencode, `-s`, same id). Frontend chases `result.session_id` (AD-3, SPECS.md).
- Gitflow: scaffold on `main` → Phase A on `feature/agent-backend-seam` → merged to `develop`.

## Completed — 2026-07-22 (Tier 3 first-half + session parity)
- **plan ↔ build mode toggle, sticky per-session** (Tier 3, first half). Seam `TurnOptions(mode)`
  threaded frontend→send→build_args; claude maps `mode=plan` → `--permission-mode plan` (agent plans,
  no edits) vs build → `bypassPermissions`; opencode ignores. `sessions.mode_for/set_mode` persist in
  the registry, re-applied after `remember()`. Footer leads with the mode. Callbacks prefix-routed
  (`^mode:`/`^resume:`). Refactor: extracted shared dispatch→deliver tail into `_run_and_deliver`.
- **Segmented mode button** — replaced the single flip-button with a 2-button control: BUILD left /
  PLAN right (fixed), selected one bracketed `[ BUILD ]`; only the bracket moves. Callback carries the
  target mode (`mode:<target>:<sid>`); identical-markup edit guarded.
- **Session parity bot↔VSCode via canonical stores** — `/resume` stopped reading only the private
  registry; new seam `AgentBackend.list_sessions(cwd)` aggregates each backend's own store: claude
  scans `~/.claude/projects/<cwd>/*.jsonl`, opencode reads `opencode.db` (session table). Sessions
  shown are adopted into the registry (backend+title, mode preserved) so a tap resolves backend for
  reply-to-continue. Bot-created claude sessions now pass `--name`. Live: 108 claude + 58 opencode
  sessions listed for /mnt/workspace. **Caveats found live (see ROADMAP "Up next"):** claude title
  should use the `aiTitle` event not the opening prompt; `--name` did NOT surface bot sessions in
  VSCode/terminal pickers (deeper filter); button feedback ~2s; `/resume` needs the 3-line redesign.
- **resume picker tweak + test sync** — adopted Lucas's hand-tested `resume.py` edits (ellipsis
  `…`→`. . .`, dropped `↳` marker), synced the 2 pinning tests.

## Completed — 2026-07-23 (P2 + P2.1 + panel iterations, all live-tested)

### P2 — backend + model + effort selection (shipped, 139 tests at ship)
Plan + measurements in [ROADMAP-p2.md](ROADMAP-p2.md). Design: SPECS AD-10 (both CLIs expose
mode/model/effort), AD-11 (capability declaration — the frontend offers only what a backend
declares; harness is chosen once at /new and cannot change mid-session; two scopes, one panel),
AD-12 (opencode /resume parity from sqlite — `tokens_*` are lifetime totals not occupancy, so
context % comes off the last assistant message per AD-9). Seam gained `TurnOptions.model/effort`,
`AgentBackend.capabilities()`/`efforts(model)`/`session_detail()`. claude maps `--model`/`--effort`;
opencode maps `-m`/`--variant`/`--agent build|plan`. claude shows 3 aliases flat; opencode a
shortlist plus provider→paged drill-down. Money lever: a throwaway phone question routes off a
metered model in one tap.

### P2.1 + rounds 3-4 — panel redesign under live feedback
- **Layout**: gear → `+`; positional grid, ≤4 buttons/row, first `+`/`‹`, last `···`/`−`, rows
  split evenly. A fixed 5-column grid (padded with invisible cells for squareness) was tried and
  dropped same day — 5 cols meant ~8-char labels and model ids stopped being distinguishable.
  SPECS AD-13. `/new` carries the panel in one bubble, giving up ForceReply's auto-focus (one
  reply_markup per message), AD-14.
- **Harness is /new-only** (AD-11 revised): no CLI imports the other's transcript (opencode has
  export/import, claude has no counterpart), so a lineage can't change harness. Killed
  `next_backend` + the switch toast + the new-session-on-switch path.
- **Vocabulary**: `provedor`→`harness`; `provider` now means who supplies the key (nvidia,
  openrouter). Buttons English.
- **Navigation**: `x`→`‹` (back one level, not jump to root); paging on `«` `»` so back and
  previous-page stop sharing a glyph. A selection redraws the state it was made in (panel-state
  stored per message, since callback_data has no room). Selected value pinned first when the list
  truncates — a bug the render exposed (`low medium ···` while `high` was set).
- **effort hidden when the model declares none** rather than answering with an alert.
- **The bug behind that alert (AD-15)**: systemd --user runs with the login PATH, so `opencode`
  (in `~/.opencode/bin`) was invisible → empty catalogue → generic empty-list message on the
  *model* button. Same gap would have failed any opencode turn. `backend/binaries.py` resolves
  every CLI explicitly (PATH first, then install dirs). 458 models under systemd, previously 0.
- **Shortlist from real usage (AD-17)**: 30 days of opencode history ranked by sessions (top three
  91/42/15) replaced a curated guess that offered once-used models; intersected with the configured
  catalogue.
- **Provider-qualified labels (AD-16)**: `nv·glm52` — `glm-5.2` exists under four providers in
  Lucas's history, so unqualified buttons would collide. `frontend/labels.py` compresses
  progressively and only on overflow (separators incl. version dot out, noise tokens dropped, alpha
  tokens contracted keeping version digits, hard cut); `config.json` `model_aliases` overrides by
  hand. Prefix dropped inside a single provider's page.
- **effort collapsed shows `medium high`** by name (opencode vocabularies are irregular); expanded
  keeps the ordinal ladder.

Rejected: scrolling/marquee button text (a label is static; animating = one editMessageReplyMarkup
per frame at ~1.5 s each → sub-1 fps, flood control). The only richer Telegram component is a Web
App webview needing an HTTPS page — noted if buttons ever stop being enough.

Refactors forced by the 200-line gate: `sessions.py` → `registry.py` (knobs) + `sessions.py`
(listing) + `keyboard.py`; `panelmenu.py` → `choices.py` (what a scope may be offered) +
`panelmenu.py` (drawing); `registry.py` → `registry.py` + `msgmap.py` (message_id→value maps).
mode.py absorbed into the panel. 166 tests at session end.
