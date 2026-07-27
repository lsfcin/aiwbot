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
