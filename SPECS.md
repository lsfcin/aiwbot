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

## Conventions
- Style R1–R6 (see code/CONTEXT.md). Files <200 LOC. Facade imports only via `backend/__init__.py`.
- Free tests must stay green to commit; live smoke (`make smoke`) is manual and costs money.
