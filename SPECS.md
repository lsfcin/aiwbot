# aiwbot — Specs

## Architecture Decisions

### AD-1 — The seam is `AgentBackend.send() -> AsyncIterator[AgentEvent]`
Every backend is a CLI subprocess emitting JSON we normalize into `AgentEvent(kind, text, tool,
session_id, cost_usd)`. `kind ∈ {text, thinking, tool, result, error}`. Minimum contract
(`check_contract`): ≥1 `text` event AND a terminal `result` carrying `session_id`. This is the ONLY
thing the frontend depends on — providers are interchangeable data behind it.

### AD-2 — `CliBackend` holds `send()` once; subclasses supply `build_args` + `parse`
Avoids per-backend duplication of the subprocess loop and run-result handling (`proc.events_from_run`).
`parse_events` stays a module-level pure function per backend → free to unit-test with fixtures.

### AD-3 — Both backends keep one lineage; the frontend still chases `result.session_id`
**Revised 2026-07-21** (Phase B). Both backends now resume into a SINGLE lineage — one session id,
one transcript, one VSCode entry that grows in place: **claude** via plain `--resume <id>` (same id
back), **opencode** via `-s <id>` (same id). Earlier this doc claimed `--fork-session` was mandatory
for claude — that was true only in the old bot's `--bg` era, where a live/registered background agent
locked the session id and refused a plain `--resume`. Phase B dropped `--bg`: `send()` is a one-shot
`-p` subprocess that exits after each turn, so the session is never locked between turns and plain
`--resume` succeeds (verified live). Forking was producing cumulative VSCode sessions (N forks = N
entries) for no benefit, so it's gone — this also matches linuz90's SDK design (plain resume, capture
id once; see [[reference_linuz90_bot]]). The frontend still stores the latest `result.session_id` each
turn and the seam surfaces it uniformly — that contract is unchanged and cheap insurance even though
both ids now happen to be stable. **Edge case**: plain `--resume` IS refused if that exact session is
concurrently open live elsewhere (interactive VSCode / a still-running agent) — the frontend detects
the busy/not-found error and shows a "close it there first" message rather than a raw error.

### AD-4 — cwd must be pinned on dispatch
Subprocesses run with explicit `cwd` (not the daemon's inherited $HOME) or the session registers under
the wrong directory and becomes invisible to later lookups. Carried from the workspace-bot cwd bug.

### AD-5 — Telegram `InlineKeyboardButton` labels don't render multi-line
Discovered live (2026-07-22): a `\n` inside a button's `text` doesn't produce a multi-line button —
Telegram clients render everything as one line and truncate it. Any "rich" per-item display (title +
preview + meta) has to live in the *message text* instead, where `\n` works normally; buttons stay
single-line tap targets, order-matched to a numbered list in the text (see `frontend/resume.py`).

### AD-6 — Session listing sources from each backend's own store, not a private registry
The `/resume` picker aggregates `AgentBackend.list_sessions(cwd)` across backends so it sees sessions
started anywhere, not just ones the bot created. Stores: **claude** =
`~/.claude/projects/<cwd with / → ->/*.jsonl` (one file per session, id = filename stem, timestamp =
mtime); **opencode** = `~/.local/share/opencode/opencode.db` sqlite `session` table (top-level rows
where `parent_id IS NULL`, `time_updated` is ms). The bot's own `config.json` registry is now only
side-state — sticky `mode`, `reply_map`, and an `adopt()` cache (backend+title) written for shown
sessions so a later tap resolves the backend for reply-to-continue.

### AD-7 — Claude Code's picker title is the `aiTitle` event (not the opening prompt)
Discovered live (2026-07-22). A session's transcript carries a recurring `"aiTitle":"…"` jsonl event
— the AI-generated title Claude Code's own `/resume` shows (e.g. `Resume video tool core M4
implementation`). The **latest** occurrence is the current title. Deriving a title from the opening
`last-prompt` instead (as the first cut did) yields ugly labels like `[A06] ## RESUME —`. Prefer
`aiTitle` (tail-scan), fall back to `lastPrompt`.

### AD-8 — `--name` does NOT make a headless `-p` session visible in Claude Code's picker
Discovered live (2026-07-22). A bot-created session passed `--name "JUST A TEST"` appeared **only** in
the bot's own `/resume` — never in VSCode `/resume` nor terminal `claude --resume`, despite a valid
`.jsonl` transcript existing in the project dir. So `-p` sessions are systematically hidden from Claude
Code's native picker by a filter internal to the (closed) extension/CLI — the name flag doesn't
override it. Making bot sessions natively resumable elsewhere is an open investigation (ROADMAP), not a
solved feature; may be impossible from outside the extension.

**SOLVED 2026-07-23 — it was an env var all along.** `CLAUDE_CODE_ENTRYPOINT` decides the recorded
entrypoint; the `-p` flag does not. A bare headless run under systemd inherits nothing → `sdk-cli` →
hidden. Setting `CLAUDE_CODE_ENTRYPOINT=claude-vscode` on the subprocess makes a bot-created session
appear in the native VSCode/terminal picker like any other. Verified live: two headless `-p` sessions
created seconds apart, one with the var (`8c5aabce`, origin `claude-vscode`) and one without
(`26d440e7`, origin `sdk-cli`) — the first is listed by `claude --resume`, the second is skipped.
`ClaudeBackend.env()` now returns it (the seam gained `CliBackend.env()` + `run_capture(extra_env=…)`,
so this stays provider-specific data, not a global). The value `cli` is **rejected** — it silently
falls back to `sdk-cli`; only `claude-vscode` works.

The filter keys on the session's **originating** entrypoint, not later entries: a session created
interactively stays listed even after headless `-p` turns append to it, and a session born `sdk-cli`
stays hidden even once `claude-vscode` entries are appended. So the var matters at session creation
(`/new`, explicit or via the "bot" prefix); already-created bot sessions stay hidden forever.

Superseded reasoning kept below, since the sub-findings still hold:

1. **The filter is real and `--name` does not beat it.** Captured the terminal picker's actual list and
   diffed it against `~/.claude/projects/-mnt-workspace/*.jsonl` sorted by mtime: every `claude-vscode`
   /`cli` session appears in exact mtime order, and **every** `sdk-cli` session is skipped — including
   `5fbc1770`, which *does* carry a `custom-title` record written by `--name`. So `--name` reaches the
   store but not the picker. The discriminator is `entrypoint` (`sdk-cli` for any `-p`/SDK invocation,
   stamped by the CLI itself; headless turns also uniquely carry `promptSource:"sdk"` + `permissionMode`).
   The bot has no flag to change it → **cannot be listed** in Claude Code's native picker.
2. **But bot sessions ARE resumable by explicit id.** `claude --resume 5fbc1770-…` from the terminal
   resumed a bot-created session and answered normally (verified live). They are unlisted, not
   inaccessible. → Hence the **reattach hint**: the `/resume` anchor message shows a copyable
   `<code>claude --resume &lt;id&gt;</code>` (`format.reattach_cmd`, provider as data — opencode maps to
   `opencode -s &lt;id&gt;`). That is the sanctioned escape hatch out of the bot.
3. **Why bot sessions once DID show up in VSCode** (Lucas's recollection, reconciled): the old `--bg`
   era started each turn as a **background agent**, which registers in the live roster
   `~/.claude/sessions/<pid>.json` (`kind`, `entrypoint`, `name`, managed by `claude agents`) and thus
   surfaced in the extension *while running*. That registration is pid-scoped and dies with the process,
   and it is exactly what forced `--fork-session` (AD-3) → one extra session per message. Visibility and
   single-lineage were a direct trade-off; Phase B chose lineage.

~~Full native visibility is only available through Claude-Code-native transports.~~ Wrong — see the
env-var fix above. Remote Control / Channels remain rejected for lock-in ([REFS.md](REFS.md)), but they
are no longer the only path to native visibility.

### AD-9 — Context % is free: it already rides in the result object
`claude -p --output-format json` returns `modelUsage[model]` carrying **both** the token breakdown
(`inputTokens` + `cacheReadInputTokens` + `cacheCreationInputTokens` = occupancy) **and**
`contextWindow`. We already parse that object every turn, so reporting `X%` costs zero extra tokens —
no `/context` call, no estimation. Plumbed as `AgentEvent.context_used`/`context_window` →
`TurnResult` → footer.

Transcripts (`.jsonl`) carry the same usage numbers in snake_case on each assistant message but **not**
the window. So for the `/resume` list the frontend pairs transcript usage with a window *learned* from
live turns (`sessions.remember_context_window`, keyed by model) instead of hardcoding per-model
constants. Unknown model → the `%` bit is simply omitted, never guessed.

### AD-10 — Both CLIs expose mode, model AND effort; the seam can carry all three
Verified live 2026-07-23 (`claude --help`, `opencode run --help`, `opencode agent list`,
`opencode models`), settling the "unverified" note that was blocking the backend/model/effort design.

| knob | claude | opencode |
|------|--------|----------|
| mode | `--permission-mode plan\|bypassPermissions\|acceptEdits\|auto\|manual` | `--agent <name>`; `build` and `plan` are both **primary** agents (also `compaction`, `summary`, `title`; `explore`/`general` are subagents) |
| model | `--model` — alias (`opus`, `sonnet`, `fable`) or full id | `-m provider/model`; `opencode models` lists **478** across providers (`anthropic/*`, `google/*`, `alibaba-coding-plan/*`, free `opencode/*` tiers…) |
| effort | `--effort low\|medium\|high\|xhigh\|max` | `--variant` — "provider-specific reasoning effort, e.g. high, max, minimal" |
| title | `--name` | `--title` |
| fork | (dropped, AD-3) | `--fork` |

Consequences for the design:
1. **The earlier claim that opencode has no plan/build equivalent is false** — it was asserted in
   `opencode.build_args`'s docstring and repeated in the roadmap. `--agent plan` is a one-flag map.
2. **Capability declaration is still the right shape**, but as a per-backend mapping table, not an open
   question. What genuinely differs is *cardinality*, not existence: claude's model set is a handful of
   aliases, opencode's is 478 — so the model picker cannot be one flat keyboard. Provider→model
   drill-down, or a curated favourites list plus a typed escape hatch.
3. **Effort values do not share a vocabulary** (`low..max` vs `minimal|high|max`), which is exactly why
   it belongs behind the seam as provider data — the frontend offers whatever the backend declares.

### AD-11 — Capability declaration: the frontend offers only what a backend declares
Shipped with P2 (plan + measurements: [ROADMAP-p2.md](ROADMAP-p2.md)). AD-10 established that both
CLIs expose mode, model and effort; AD-11 is how that reaches a keyboard without the frontend
learning any provider's vocabulary.

**The seam gained two declarations and two knobs.** `TurnOptions` carries `model` + `effort`
(opaque strings), and `AgentBackend` answers `capabilities() -> Capabilities(modes, favourites,
groups)` plus `efforts(model) -> list[str]`. The frontend renders exactly what comes back and
invents nothing, so a value the CLI would reject can't be tapped.

**Effort is asked per model, not per backend, because that is how it varies.** `models.json`
declares `reasoning_options` per model in four shapes — `effort` with values (1578 models),
`toggle` (939), `budget_tokens` (502), absent (3311) — and the `effort` value sets themselves
differ (`low,medium,high` · `high,max` · `minimal,low,medium,high` · `low..max`). claude is the
easy case: one `--effort low|medium|high|xhigh|max` ladder for everything. The non-effort shapes
declare `[]`, and the panel says so out loud instead of drawing a row of values `--variant` would
refuse.

**Cardinality, not existence, is what differs** (AD-10's phrasing) — so the model picker is
`favourites` + a `groups` drill-down: claude's 3 aliases ARE its whole catalogue and the `mais…`
button never appears, while opencode's 478 across 6 providers page 6 at a time.

**Harness is chosen once, at `/new` — it is not a per-session knob.** *Revised 2026-07-23
(Lucas).* The first cut offered a harness switch on a live session, mapped to "arm it, and the next
turn opens a fresh session there". That was answering a question nobody asked: switching only means
something if the context comes along, and it cannot. `opencode` has `export <sessionID>` /
`import <file>`, `claude` has no counterpart at all — so claude→opencode would mean rewriting a
transcript into opencode's JSON schema, and the return trip is impossible. A lineage therefore
belongs to its harness for life (AD-3), and the session panel offers only **model** and **effort**.
Harness lives in the `/new` scope, alongside the model and effort a fresh session inherits.

**Two scopes, one panel.** Knobs are addressed by *scope*: a session id, or the sentinel
`registry.NEW` for the session `/new` is about to create. `NEW` reads and writes the `defaults`
block, which every finished turn overwrites — so a new session starts on the last interaction's
harness/model/effort. The panel code is scope-agnostic; only `registry` knows there are two stores.
`/new --backend X` writes the same `NEW` knob the button does, so typing it and tapping it are the
same act on the same state.

**Vocabulary.** `harness` = the CLI (claude, opencode). `provider` = who supplies the key (nvidia,
openrouter, google) — the sense opencode itself uses, and the level the model drill-down groups by.
Calling the harness a "provider" (the first cut did) collides with that. Button labels stay English
(`harness` · `model` · `effort`), matching `BUILD`/`PLAN`, which were already English.

**Panel taps spend no callback_data on the session id.** The panel always edits the anchor
message, and `reply_map` already resolves that message_id → session_id, leaving all 64 bytes for
values. `p:s:m:openrouter/qwen/qwen3-coder-next` fits with room to spare.

### AD-12 — opencode's store answers the picker, but only per message for context %
Picker parity with claude (3-line entry: title / preview / meta) reads opencode's sqlite:

| bit | source |
|-----|--------|
| mode | `session.agent` |
| model | `session.model` JSON → `providerID/id`, the same form `opencode models` and models.json use |
| context window | `models.json` → `limit.context` |
| preview + context used | last `message` with `role=assistant`: its `type=text` parts, and `data.tokens` |

Two traps, both hit live:
1. **`session.tokens_*` are lifetime totals, not occupancy.** A real session summed to 350 927
   against a 200 000 window — 175%. Occupancy is per message (`input + cache.read + cache.write`,
   the same formula AD-9 uses for claude), so it comes off the last assistant message.
2. **`part` rows of `type=text` include the user's message and injected system-reminders.**
   Filtering by the parent message's `role` is what stops the preview quoting Lucas back at himself.

Because those two need a query per session, the seam gained `session_detail(session_id, cwd)`:
`list_sessions` stays the cheap index, and the picker asks for detail only on the page it renders
— 3 sessions, not the 59 that exist.

### AD-13 — Panel layout: at most four per row, framed by two controls
*Lucas's design, 2026-07-23 — second iteration.* The first cut was a fixed 5-column grid padded
with invisible braille-blank buttons, chosen so every cell was square and column N of one row sat
above column N of the next. **Abandoned the same day**: Telegram divides a row's width evenly
between its buttons, so five columns meant ~8-character labels, and model ids truncated past the
point of telling apart (`claude-fable-latest` vs `claude-haiku-latest`). Lucas: *"desisti do grid,
tá custoso em termos de usabilidade."*

The rule now is positional rather than geometric:

- **At most four buttons per row, and rows may hold fewer.** No padding — a shorter row simply has
  wider buttons. Labels get ~12 characters instead of ~8.
- **The first button is always `+` (open) or `‹` (back one level).** It was an `x` that jumped
  straight to the mode row; Lucas replaced it 2026-07-23 because a single control that always
  cancels reads wrong inside a tree — `‹` walks menu → values → providers → a provider's models
  back up one step at a time.
- **The last button is always `···` / `−`** (expand / collapse the value list), wherever it lands.
- So a collapsed picker is one row of `x`, **two** values, `···` — or **three** values when the
  list fits and there is nothing to expand.
- Rows split **evenly**, not greedily: five buttons become 3+2, never 4+1. Width is shared inside a
  row, so a greedy tail would stretch one lone button across the whole bubble.
- The pager is a row of its own (`‹ N/M › −`), which is what keeps the collapse control last.

Two behaviours this layout forces, both discovered by rendering the real states:

1. **The selected value is pinned first whenever the list is truncated**, including when it was
   chosen in the drill-down and is not in the shortlist at all. Two visible slots out of five means
   a picker showing `low medium ···` while `high` is set — invisible state. Selected-first is the
   one rule that always shows it.
2. **`‹` and `«` are different controls.** Back-one-level and previous-page both sit in the
   leftmost slot of their row, so identical glyphs would stack vertically meaning two different
   things. Paging uses the double angles `«` `»`.
3. **A dimension with nothing to offer is not shown at all.** `effort` disappears from the menu
   when the chosen model declares no effort vocabulary — including opencode before any model is
   picked, where the vocabulary is simply unknown. This replaced an alert saying "esse modelo não
   expõe controle de esforço", which was both unreachable-by-intent and, worse, was the generic
   message for *any* empty list (see AD-15).

The mode row is not a picker and keeps fixed positions: `+ [ BUILD ] PLAN`, only the bracket moves.

### AD-14 — `/new` gives up ForceReply to carry the panel
Telegram accepts exactly **one** `reply_markup` per message: `ForceReply` *or* an inline keyboard,
never both. A bare `/new` used to send a `ForceReply` (which focuses the keyboard and pre-anchors
the reply); carrying the harness/model/effort grid means giving that up. Lucas chose the single
bubble with buttons (2026-07-23), so `/new` now answers with a config bubble you adjust and then
reply to by hand. `/new <prompt>` and the `bot ` prefix are unchanged: they start immediately on the
inherited defaults.

### AD-15 — systemd's PATH is the login default, so every CLI is resolved explicitly
Found via a wrong error message, 2026-07-23: tapping **model** with harness=opencode answered
"esse modelo não expõe controle de esforço". Two faults stacked. The visible one was a single
generic message used for any empty value list. The real one: `systemd --user` runs with the login
PATH, which does **not** carry the per-tool bin directories a shell rc adds — `opencode` lives in
`~/.opencode/bin` and was simply invisible to the service. `opencode models` never ran, the
catalogue was empty, and the picker had nothing to show.

The same gap would have failed any opencode **turn** outright, since `build_args` emitted a bare
`"opencode"` for `create_subprocess_exec`. Only claude worked, and only because it resolved its
binary explicitly already.

`backend/binaries.py` now does that resolution for every backend: PATH first (so a shell override
still wins), then the known install locations per tool. `resolve()` raises, `find()` returns None
for callers that degrade. Verified inside a real `systemd-run --user` unit: 458 models listed,
previously 0. The count differs slightly from a shell's 478 because a couple of providers key off
environment the service does not inherit — which is correct behaviour, since the picker should
offer only what the process running the turn can actually reach.

### AD-16 — Model labels: qualify by provider, compress only on overflow
The same model name appears under several providers — Lucas's own 30-day history has `glm-5.2`
under `nvidia/`, `openrouter/`, `opencode/` and `ollama-cloud/`. An unqualified shortlist would
therefore show two buttons reading `glm-5.2` that do different things. So a model button is
`<provider>·<model>`, with two-letter provider abbreviations (`opencode`/`openrouter` share a
four-letter prefix, so the map is chosen data, not a mechanical prefix).

The budget is about twelve characters. `frontend/labels.py` spends it progressively, and **a name
that already fits is never touched** — an abbreviation you have to decode costs more than a long
name you can read:

1. separators out, **including the version dot** → `glm-5.2` → `glm52`, `kimi-k2.6` → `kimik26`
   (Lucas: "I'll know that 52 means 5.2" — it also stops `or·glm5.2` carrying two dots that mean
   different things)
2. noise tokens dropped (`latest`, `instruct`, `preview`, `chat`)
3. alpha tokens contracted to two letters, digit-bearing tokens kept whole →
   `deepseek-v4-flash` → `dev4fl`
4. hard cut

Contraction sits before truncation because it preserves distinctions: `qwen3-coder` and
`qwen3-coder-next` truncate to the same nine characters but contract to `qwen3co` / `qwen3cone`.
The vendor namespace (`deepseek-ai/`) is dropped entirely — the provider prefix already says it.
Inside one provider's own page the prefix is dropped too, since every row would repeat it.

`config.json` `model_aliases` overrides any id by hand. The rule gives `nv·dev4fl`; Lucas reads
that name daily and prefers `nv·dsv4f`, which is a preference no algorithm should be guessing.

### AD-17 — The shortlist is read from usage, not curated
`catalog.favourites()` ranks the last 30 days of opencode sessions by count, ties broken by
recency, intersected with the configured catalogue (a model whose provider vanished stops being
offered rather than failing at dispatch). The curated "cheap and good" guess it replaced was wrong
by a wide margin: it offered models used once each while the real top three had 91, 42 and 15
sessions. A machine with no history falls back to the cheap tiers.

The source is one query over `session.model` + `time_updated`, which opencode indexes anyway.

### AD-18 — Pipe-tables render as row blocks, never a `<pre>` box (2026-07-26)
Telegram has no table syntax at all. Boxing a table in `<pre>` (the original b1 rendering) fails
on both axes a table has: `<pre>` escapes its contents, so cell markdown freezes into literal
`**`; and it does not wrap, so it overflows. Measured over 412 tables from real agent answers,
**95% carried inline markdown** and **0 of 412** fit a phone-width monospace bubble (median widest
row 151 chars) — so there is no narrow case worth a second code path. `frontend/table.py` renders
each row as a labelled block (`<b>name</b>` then `header: value` lines), labelling values only when
a row has siblings to tell apart. See KNOWN-BUGS b1 (archived in HISTORY 2026-07-26).

### AD-19 — STT: one punctuated carrier prompt, plus a confidence hallucination guard (2026-07-26)
Whisper imitates the style of what it is primed with, so punctuation is bought by a punctuated
`initial_prompt`, not by any decode flag. But `initial_prompt` and faster-whisper's `hotwords=`
share one conditioning slot, so the jargon rides *inside* a punctuated carrier (`hotwords.CARRIER`)
rather than in a competing arg — priming for punctuation alone had turned "bote" into "Pode".
Separately, Whisper hallucinates words on near-silent audio and no decode setting stops it (VAD
only shortened the garbage), so the guard is the model's own `avg_logprob`: real transcripts scored
-0.15..-0.48, garbage -1.49, threshold `_MIN_LOGPROB = -0.9`; a rejected transcript rides the C3
fail-safe. `no_speech_prob` is 0.000 for every file once VAD strips the silence — not a usable
signal. Corollary convention: **`format.plain` is `html.escape`, never speech** — TTS input goes
through `speech.to_speech`, not `plain`. Contract in `frontend/SPEC.md`.

### AD-20 — A panel tap costs exactly one Telegram round trip (2026-07-27)

Measured, not reasoned about: bot-side work on every warm callback path is **under 1 ms**, while
one call to `api.telegram.org` is **222 ms** median from Lucas's machine. Anything that felt slow
about a button was therefore a count of round trips, never our compute — and the count was wrong
in three places (two sequential calls per tap, three on a value choice, plus an 839 ms
`opencode models` shell on the first tap after each restart).

The rule that follows: **one tap issues one `answerCallbackQuery` and at most one
`editMessageReplyMarkup`, concurrently.** `panel._redraw` is the single place both are sent, via
`asyncio.gather`; `_route` threads a choice's toast through as an argument so no branch is tempted
to answer a second time. Anything a backend computes to draw a keyboard is warmed at startup
(`choices.warm`, through the seam) rather than lazily on the button.

This is a floor, not a target: a Telegram client renders an inline keyboard purely from server
state, so no local echo or optimistic client update exists to beat one round trip. The button's
built-in spinner is the only instant feedback there is, and clearing it is already what
`answerCallbackQuery` does. `concurrent_updates(True)` is deliberately **not** enabled — it
overlaps separate taps but does nothing for a single tap's latency, while widening the race on
`config.json`'s non-atomic read-modify-write. Regression spec: `tests/test_f3c_tap_latency.py`
asserts the round-trip *count*, since the duration is not ours to hold.

### AD-21 — The STT conditioning prompt is prose, end to end (2026-07-27, corrects AD-19)

AD-19 shipped `initial_prompt` as punctuated carrier sentences **followed by the bare `HOTWORDS`
list**, reasoning that the two only had to share one conditioning slot. Measured against Lucas's
chuveiro voice note, that shape scores **0.0 punctuation marks per 100 words** — the priming
failed outright, and he reported it as "punctuation didn't work".

Three prompt shapes, same audio, same model:

| prompt shape | punctuation | `claude sonnet` |
|---|---|---|
| sentences, then bare word list (AD-19, shipped) | **0.0**/100w | ✗ `claudsonner` |
| bare word list, then sentences (tail punctuated) | **1.1**/100w | ✓ |
| jargon dissolved *into* the sentences | **22.5**/100w | ✓ |

The middle row is what kills the obvious theory: the carrier sat at the tail, where whisper
weights hardest, and punctuation still died. **A bare word list anywhere in the prompt suppresses
punctuation.** So the rule is: the conditioning prompt is prose from end to end, and the way to
teach the STT a new word is to put it in a sentence someone could have said. `HOTWORDS` survives
as the *checklist* — the existing coverage test now doubles as the guard that every listed word
really appears in a sentence.

Second, independent cause of the same complaint: **no model name was in the vocabulary at all** —
no `claude`, no `sonnet`, no `opus`. `claude sonnet` had nothing to anchor to, came back as
`claudsonner`, and so the F3a spoken directive silently never fired. Naming a model out loud is a
first-class way to steer a turn, so the models belong in the primed vocabulary like any jargon.

### AD-22 — A picker reorders only to rescue a hidden selection (2026-07-27)

`_ordered` hoisted the current value to the front unconditionally, so every model pick reshuffled
the buttons under Lucas's thumb. The behaviour exists for a real reason — a picker that hides
what is set is worse than one that reorders — but that reason only applies when the selection
would fall outside the drawn slots. Claude's handful of aliases all fit on one row, so there was
nothing to rescue and the motion was pure noise. Hoisting is now conditional on the selection
actually being cut off; a list that already shows its selection keeps its declared order.

### AD-23 — An answer is a conversation, and every bubble of it is repliable (2026-07-27)

Two rules, and the second is what makes the first safe.

**Long answers split at paragraph boundaries on purpose.** Not as a 4096 rescue — as the shape of
the thing. Lucas: *"talvez fosse até uma estratégia de UX partir a resposta em várias mensagens
pra parecer mais como uma conversação"*. `split_html` takes a soft size (`reply.SOFT_CHARS = 900`)
past which the chunk ends at the next blank line, so a bubble never stops mid-thought; Telegram's
hard cap still wins, and a run of blank lines can never seal an empty chunk. The same path
delivers the `/resume` anchor, which is why `ANCHOR_BODY_MAX` is gone: that 3000-char mid-word
clip, not Telegram's limit, produced the `[…]` Lucas reported.

**Every message the bot sends for one turn anchors to that turn's session.** `reply.deliver`
returns all of them and callers map all of them, because Lucas replies to whichever bubble he
happens to be reading, not to the last one. Anchoring only the tail meant a reply to an earlier
bubble missed `session_for_reply` and fell through to INBOX capture — the turn silently did not
continue. That failure is *created* by splitting, so the two rules ship together and the message
map is sized for bubbles (`msgmap.MAX = 400`), not for turns.

**Corollary, reversing F2's reply anchor.** F2 led every answer with `continua [ABC] TÍTULO`
because Telegram quotes a message from its start, so the session name had to be the first line.
The reasoning was sound and aimed at the wrong reader: the bot's answer is already `do_quote`d
onto Lucas's own message, so the thread is visible without announcing it. The line is deleted,
not demoted; the id and title live in the footer (`[ABC] TÍTULO · claude · sonnet · build ·
$0.031`), which is where he asked for them. `answer.py` now owns the answer message's shape —
`format.py` stays shared text formatting, and the split is what kept it under the size gate.

### AD-24 — Occupancy is the last request; anything summed is spend (2026-07-27, b3)

A turn is not one API request. A turn that uses tools makes several, and each one re-reads the
whole conversation from cache — so **any total over a turn measures money, and only the last
request measures how full the window is.** Summing them put 100–200%+ in the footer of Lucas's
answers; over real transcripts the same sum reaches 5921%, 6507% and 32533%. The denominator was
never the problem — the learned windows were a correct 1,000,000.

The subtle part, and the reason this is a spec and not a patch note: the wrong number is *not
always visibly wrong*. One real session summed to a perfectly plausible 62% when the truth was
5%. A bug that only sometimes looks like a bug is one that survives review, so the rule is
structural rather than a range check.

It lives on the seam, as `CliBackend.occupancy(session_id, cwd)` — every CLI records a
per-message token breakdown in its own store, so each backend reads occupancy from there and the
run's summary object is never trusted for it. claude takes the transcript's last assistant
message; opencode takes `ocstore.last_turn`, which is also the first time an opencode answer
reports a percentage at all. `ocstore.py` had documented this exact trap for opencode's
accumulating `tokens_*` columns and the claude path walked into it anyway — one backend
remembering a rule is not the same as the seam enforcing it.

Belt and braces on top: `format.context_pct` withholds any share above 100%, because a share of
the window cannot exceed the window. A visibly missing number is a better bug report than a
confidently wrong one.

### AD-25 — Streaming seals bubbles; it never rewrites one (2026-07-27, F4 Stages 1–3)

Painting an answer as it arrives could easily have contradicted AD-23, which says a long answer is
several bubbles and every one of them is repliable. It does the opposite — it makes AD-23
*continuous* — and the reason is a property, not a convention:

**`split_html` is prefix-stable.** Its loop is a single forward pass whose seams are decided only
from lines already consumed, so appending text can change nothing but the **last** chunk.
Property-tested over 25 corpora × every line-boundary prefix of each: zero violations. Therefore
every chunk but the last is already final, and a bubble can be sent the moment it appears and
**never touched again**. Each is anchored on arrival rather than at the end of the turn, so a
reply to bubble 1 continues the session while bubble 3 is still being written — strictly better
than the batch path, which could only anchor once everything existed.

Three rules follow, and they are the ones to preserve:

1. **Only text that can no longer change is rendered.** `markdown.stable_prefix` settles
   everything up to the last blank line *outside an open code fence* — a parity count, not a
   regex, because inside a fence a blank line is code, not a paragraph break. The unsettled tail
   rides as escaped plain text; rendering it would make it flicker between literal and formatted
   as closing markers land.
2. **One code path for streamed and finished.** `answer.block` delegates to `answer.frames`, so
   the shipped answer *is* a frame with no pin and a footer. That is what makes the AD-23
   non-regression test meaningful rather than two implementations that happen to agree today.
3. **Throttling drops, never queues.** The gate is a clock check inside `paint()`, not a
   background ticker, so nothing races the end of the turn. A paint already in flight is
   discarded, which is lossless because every frame recomputes from the whole accumulated text —
   and it is what stops a fast stream from piling requests up behind a ~200 ms round trip (AD-20).

The cadence itself (`MIN_INTERVAL`, `MIN_GROWTH`) is a **UX knob Lucas tunes by reading real turns
in the chat**, not a rate-limit constant — it went 1.5 s → 5 s → 3 s in one session. Tests pin the
*spacing invariant against the constant*, never a literal, so tuning never edits a test. Telegram's
native `ChatAction.TYPING` carries the gap between repaints and is deliberately lit on the FIRST
delta, independent of the repaint gate, so the wait before the first visible words is never silent.

Streaming stays behind `TurnOptions.stream` because it changes the CLI's invocation: the rollback
has to be reachable from Lucas's phone — one line in `config.json` plus a restart, never a code
change. `painter.STREAM_SEAL` is the finer-grained rollback that gives up sealing while keeping
live text.

### AD-26 — The bot hosts the MCP server; the turn is named by the URL (2026-07-27, F4 Stage 4)

`ask_user` only works in linuz90's bot because the SDK runs the agent **in-process**: its tool
handler awaits a button press in the same process that owns the chat. aiwbot drives a
**subprocess CLI**, the opposite shape — a stdio MCP server would be spawned *by* that CLI, a
child of it, with no way to reach the daemon's Telegram state.

So the relationship is inverted: **the daemon hosts an HTTP MCP server in its own event loop, and
each turn points its CLI at it** (`--mcp-config '<json>' --strict-mcp-config`). The handler runs
where the chat already lives, blocks the agent's turn exactly like the in-process version, and no
Phase D rewrite is needed. It is plain JSON-RPC 2.0 over `aiohttp` — the `mcp` SDK would be a new
dependency for ~40 lines.

**The turn a question belongs to comes from the URL path** (`/mcp/<token>`), never from the
payload: an MCP request carries no turn id, and turns run concurrently as PTB tasks, so there is
nothing else to correlate on. The token is registered before the backend starts and released in a
`finally`, so it cannot outlive its turn. Two consequences that are easy to get wrong:

- **The handshake must be a pure function of the request.** Measured: one `claude -p` run sends
  `initialize` *three times*. A server holding per-connection state would answer the repeats from
  a half-built session.
- **`--strict-mcp-config` is not optional.** Without it the turn also loads whatever MCP servers
  Lucas configured for interactive Claude Code — a different tool surface than the one the turn
  was reasoned about with.

### AD-27 — An unanswered question returns text, and plan mode cannot ask at all (2026-07-27)

Two limits of the CLI, both measured against the binary rather than read off documentation, both
load-bearing:

**The tool call dies at ~60 s** ("Tool timed out. No answer got.") — nothing next to the hour
Lucas wants to answer in, away from his phone. `MCP_TOOL_TIMEOUT` (ms, in the subprocess env)
lifts it, and the bot's own `ask.WAIT_SECONDS` is set *below* the raised ceiling so the wait that
ends first is always ours. That ordering is what makes the next rule reachable:

**Every exit of a wait is a string.** Timeout, a turn that ended, a bubble Telegram refused — all
return *content* the agent can act on ("siga com a hipótese mais razoável e diga qual assumiu"),
never an MCP error. An error aborts the turn and throws away everything the agent had already
worked out; a sentence costs it one paragraph. Lucas's call, and the reason `ask()` has no raising
path at all.

**Plan mode refuses the whole MCP surface**: `claude -p --permission-mode plan` answers the call
with *"Cannot call mcp__aiwbot__ask_user while in plan mode"*, and an explicit `--allowedTools`
does **not** lift it. So `supports_ask` is a function of the *options*, not of the provider —
claude asks in build mode and never in plan. This is a real gap, because plan mode is exactly
where interviewing matters most; the substitute that measures out is
`--permission-mode bypassPermissions --tools "Read,Grep,Glob"` (read-only built-ins, MCP intact,
verified live), which trades plan mode's own prompt for the ability to ask. Not adopted
unilaterally — it changes what `mode=plan` means, so it is Lucas's call before Stage 5.

### AD-28 — Build only, so the panel opens on the knobs (2026-07-28)

Lucas took option A of AD-27: plan mode is not supported through the bot. Two things follow, and
both are the point rather than side effects.

**Mode is coerced, not offered.** `registry.mode_for` returns `build` whatever is stored, so a
session started on the PC in plan mode and continued from the phone silently becomes a build
turn instead of inheriting a mode the bot cannot honour. The knob survives on the seam
(`TurnOptions.mode`, each backend's mapping) — restoring plan is one line if a future CLI stops
blocking MCP in it — but nothing in the bot writes anything else.

**The panel lost a level.** BUILD/PLAN was a two-option segmented control with one reachable
option, and the `+` that used to open the dimension menu existed only to get past it. Both are
gone: the root keyboard IS harness/model/effort, so the panel costs one tap where it cost two.
Keyboards already sitting in the chat still carry `p:mode:*` buttons, so that callback stays
routed — to a redraw of the current panel, never to setting a mode.

### AD-29 — A bubble carries its question and its position (2026-07-28)

Three shape rules, all from Lucas reading real turns:

**The voice transcript rides inside the answer, quoted, at the top of every bubble** — not in a
bubble of its own. The standalone echo (F2) cost a message and scrolled out of reach exactly when
the answer was long enough to need it. Repeated per bubble, any bubble he scrolls back to still
says what it answers. It is escaped and clipped (`LEAD_CHARS`), because it is arbitrary speech.

**Every bubble ends with its position**, `(2/3)`. The total is unknowable while the answer is
still arriving — bubble 3 exists only once the text that fills it does — so a bubble is born
carrying `(2)`, and **one closing pass** stamps the totals once the turn ends (Lucas asked for
exact positions everywhere, 2026-07-28). That pass is the single exception to AD-25, which is why
the rule reads "a sealed bubble is not rewritten *while the answer is streaming*" rather than
"never": prefix-stability guarantees the counter is the only thing that changes, and the pass runs
after the live bubble is finished, so the answer completes first and the stamping trails it.

**Bubbles are paced apart, one per paint.** `cadence.BUBBLE_GAP` is the floor between one bubble
appearing and the next; `MIN_INTERVAL` only ever paced repaints of the live bubble, and conflating
the two is why the cadence appeared to do nothing. A stream that outruns the gap waits rather than
losing text: the held text lands whole as the next bubble. `_grow` posts **exactly one** bubble per
paint however far ahead the stream has run — posting every chunk that already fits would land
three in the same second and undo the pause. The gap is a floor, never an added delay: a stream
slower than it passes through untouched, and the first bubble is never held back, because the
working message already is bubble one.

**`·` is a divider, never an opener.** It separates (`· · ·`, `provider · modelo`), so it must not
lead a line: `pensando…`, not `· pensando…`.

The furniture is budgeted BEFORE the split, not appended after: a chunk sized to the full limit
and then given a lead and a counter is a message Telegram rejects — and only ever on the long
voice answers this exists to serve.

### AD-30 — A question ends the segment above it (2026-07-29, from the first real interview)

An `ask_user` question is its own message, so the live bubble stops being the last thing in the
chat the moment one is posted. Everything the agent writes afterwards is an answer to that
question and must appear BELOW it — a live bubble that kept growing put the answer above the
question that prompted it.

So an answer is delivered in **segments**: a contiguous run of bubbles at the bottom of the chat.
`painter.cut()` ends one — repainting the closing bubble **without the pin** (with a question
pending, a status line claims work that is actually blocked on Lucas) and deleting it outright
when nothing but the status ever reached it. The next paint opens a fresh bubble below the
question. Three consequences, each of which broke once before it was pinned:

- **The closing delivery renders only the current segment** (`painter.tail_of`). Handing it the
  whole answer reposted everything written before the question underneath it.
- **Bubbles are numbered across the answer, not per segment**, so an interview does not restart at
  `(1)` after every question. Questions are not counted — they are not answer text.
- **A bubble is recorded undecorated** (`bubbles.bare`). Restamping a chunk that already carried
  `(1)` produced `(1) (1/10)`. Telegram hands back the plain rendering of a message, never the HTML
  that was sent, so the record is the only way to restamp at all.

Every counter, split and stamp here is **string formatting in `answer.py` — zero tokens, no model
involved.** That is why it can be relied on: the shape of a reply is never something the agent
chose or could get wrong.

Two shape rules from the same session: the counter closes the ANSWER (before the footer, hard
against the final word, never adrift on its own line), and the footer never gets a bubble of its
own — an answer ending on a paragraph break used to leave a blank line before `· · ·` that the
splitter read as a place to break.

**Both of the last two bugs passed every assertion in the file** and were caught by printing the
bubbles and reading them. Eyeball the output when the shape changes.

## Conventions
- Style R1–R6 (see code/CONTEXT.md). Files <200 LOC. Facade imports only via `backend/__init__.py`.
- Free tests must stay green to commit; live smoke (`make smoke`) is manual and costs money.
