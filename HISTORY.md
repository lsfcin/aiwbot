# aiwbot — History
> Archive of completed work. Open work lives in [ROADMAP.md](ROADMAP.md).

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
