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

**A backend switch cannot move a lineage, so it opens a new session.** Only the owning provider
can resume its own id (AD-3), which makes "switch backend inside a session" impossible as
literally stated. It maps to: arm `next_backend`, and the next turn starts a fresh session on that
provider, carrying the title and the mode. Model and effort are explicitly *dropped* on the switch
— they are provider-specific strings (`opus` means nothing to opencode, `openrouter/x/y` means
nothing to claude) and carrying either across would build an argv the CLI rejects.

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

## Conventions
- Style R1–R6 (see code/CONTEXT.md). Files <200 LOC. Facade imports only via `backend/__init__.py`.
- Free tests must stay green to commit; live smoke (`make smoke`) is manual and costs money.
