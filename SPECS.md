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

### AD-3 — Session lineage differs per backend; the frontend must chase `result.session_id`
Proven live: **claude** resumes via `--resume <id> --fork-session` and mints a NEW session id each turn
(registered agents refuse a plain --resume — learned the hard way). **opencode** resumes via `-s <id>`
and keeps the SAME id. Both preserve context. The frontend must always store the latest
`result.session_id` from each turn, never the id it sent — the seam surfaces it uniformly.

### AD-4 — cwd must be pinned on dispatch
Subprocesses run with explicit `cwd` (not the daemon's inherited $HOME) or the session registers under
the wrong directory and becomes invisible to later lookups. Carried from the workspace-bot cwd bug.

## Conventions
- Style R1–R6 (see code/CONTEXT.md). Files <200 LOC. Facade imports only via `backend/__init__.py`.
- Free tests must stay green to commit; live smoke (`make smoke`) is manual and costs money.
