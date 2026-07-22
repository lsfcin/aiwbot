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

## Conventions
- Style R1–R6 (see code/CONTEXT.md). Files <200 LOC. Facade imports only via `backend/__init__.py`.
- Free tests must stay green to commit; live smoke (`make smoke`) is manual and costs money.
