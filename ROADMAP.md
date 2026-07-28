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

### F3c, voice + picker fixes, F5 ✔ **SHIPPED 2026-07-27** — archived in [HISTORY.md](HISTORY.md)
Button-tap latency cut to one round trip (AD-20); the STT prompt corrected to prose end-to-end
plus model names primed, the transcript echo restyled, and the picker stopped reshuffling
(AD-21/AD-22); the F5 answer shape — paragraph splitting, every bubble repliable, footer instead
of the `continua` anchor (AD-23).

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

**Live now:** `"stream": "true"` is set in `~/.config/aiwbot/config.json` defaults. Rollbacks, least
drastic first: `painter.STREAM_SEAL = False` (back to one freezing bubble, keeping live text) →
`"stream": "false"` + restart (back to Stage 1, no code change).

| Stage | Goal | Checkpoint |
|---|---|---|
| **0** ✔ | split `bot.py` → `turnrun.py`, zero behaviour change | everything looks exactly as before |
| **1** ✔ | streaming seam in the backend, still batch-delivered | log shows frames ticking; Telegram identical |
| **2** ✔ | live bubble: throttled painter, pin held below | text grows ~every 3 s, footer+keyboard at the end |
| **3** ✔ code | seal bubbles mid-stream (full AD-23 under streaming) | **UNCONFIRMED** — reply to bubble 1 *while bubble 2 writes* |
| **4** ✔ code | `ask_user` MCP transport, probe-gated | **UNCONFIRMED in chat** — question bubble → tap → the same turn names the choice |
| **5** | `ask_user` in anger, close F4 | a real task away from the PC — **blocked on the plan-mode decision below** |

Key risks pre-empted: 64 KB subprocess stream limit (`limit=1<<20`); stderr pipe fills and hangs the
child (sibling drain task); occupancy read before the transcript flushes would silently regress b3
(`await proc.wait()` before yielding the result event); 429 pile-up (in-flight guard that *drops*
rather than queues, plus self-tuning backoff); `bot.py` 198/200 and `claude.py` 194/200 both split
**before** gaining code.

#### Lucas's 2026-07-28 batch ✔ — decisions taken, papercuts fixed
Stage 3 **confirmed in chat** ("funciona"). Then his list, with what each turned into:
- **AD-27 decision: option A.** Build only. Mode coerced + panel opens on the knobs (AD-28).
- **`·` never opens a line** — it is a divider (AD-29), enforced by a phrase-bank test.
- **The voice transcript moved inside the answer**, quoted at the top of every bubble, and the
  standalone echo bubble is deleted along with the `TRANSCRIPT_ECHO` phrase (AD-29).
- **Bubbles say where they sit** — `(2/3)` finished, `(2)` mid-stream (AD-29).
- **A turn can no longer fail silently.** Every turn runs as a detached PTB task, so an exception
  reached stderr and nothing else — which is why one voice note simply vanished. `turnrun.guarded`
  now replies with the error instead.
- **Latent RAM bug, found and fixed:** `painter.note_session` iterated the very list `_anchor`
  appends to, so a Painter built without `on_bubble` grew it without bound — RAM until the OOM
  killer took the editor with it. Two independent fixes (snapshot-then-drain, and "nobody
  listening" no longer re-queues) plus a regression test. Never fired in the live bot, where
  `on_bubble` is always set, but it was one call site away.

Still open from that list, answers in the reply rather than in code:
- **Bubble balance** (his #2) — the split is greedy at ~900 chars because sealing forbids
  lookahead: a bubble is sent before the text that would balance it exists. Rebalancing means
  giving up sealing. Left as is, on his "podemos ignorar".
- **Pacing between bubbles** (his #3) — there is no inter-bubble delay to turn on; what exists is
  the 3 s repaint floor and the typing indicator. Nothing was broken, nothing was enabled.

#### F4 Stage 4 ✔ **code done 2026-07-28** — gate passed, live round trip proven off-Telegram
The probe the stage was gated on passed: a stub HTTP MCP server + `claude -p --mcp-config
'<json>' --strict-mcp-config` really does expose `mcp__aiwbot__ask_user` to the agent, with the
turn token surviving in the URL path. Then the real thing, end to end with Telegram faked and the
real `askserver` + broker + `CliBackend.send`: **question → buttons → tap → the same turn resumed
and named the choice, 15 s wall.** Shape and rationale are in SPECS AD-26/AD-27.

**Measured, do not re-derive:**
- A tool call is killed at **~60 s** by default. `MCP_TOOL_TIMEOUT` (ms, subprocess env) lifts it;
  the bot waits 55 min *under* a 60 min ceiling so the timeout path is always ours and always text.
- The CLI sends **`initialize` three times** per invocation → the handshake must be stateless.
- **Plan mode refuses every MCP tool** — see the decision below.
- `aiohttp` was already installed; the `mcp` SDK is still not a dependency.

Rollbacks, least drastic first: `"ask": "false"` in `config.json` + restart (turn invoked exactly
as in Stage 3) → the server failing to bind, which disables ask by itself and leaves the daemon up.

**⛔ Decision Lucas owes before Stage 5 — ask_user cannot run in plan mode.**
`claude -p --permission-mode plan` answers the call with *"Cannot call mcp__aiwbot__ask_user while
in plan mode"*; `--allowedTools` does not lift it (both measured). Plan mode is exactly where
interviewing pays off, so this is the stage's one real dent. Options:
- **A — leave it.** Ask works in build mode only; a plan-mode turn behaves as it does today. Zero
  risk, and Stage 5's "real task" has to be a build-mode one.
- **B — re-implement `mode=plan` as read-only build.** `--permission-mode bypassPermissions
  --tools "Read,Grep,Glob"` keeps the MCP tool callable and still touches nothing — verified live.
  It trades away plan mode's own system prompt (no ExitPlanMode, no plan formatting), so the
  answers will read differently. It changes what a mode Lucas uses daily *means*, which is why it
  is not taken unilaterally.

#### F4 Stages 0–3 ✔ **SHIPPED 2026-07-27** — archived in [HISTORY.md](HISTORY.md)
Stage 0 split `bot.py` → `turnrun.py` (the cut chosen by F4's seam, not by line counting);
Stage 1 made the backend stream; Stage 2 painted the live bubble; Stage 3 sealed bubbles as they
are born and anchored them on arrival. **Stage 3's live checkpoint is still unconfirmed by
Lucas** — see the table above for what to look for.

### F4 — original sketch (superseded by the staged plan above)
- [ ] **Live feedback** (Phase C, linuz90 mold) — `stream-json`: edit the message as the agent's chat
      text arrives, appending in chunks, keeping "⏳ pensando…" pinned at the END until the turn
      finishes. Builds on the ⏳-morph already shipped. Changes the reply/dispatch mechanics other
      niceties touch — hence late.
- [ ] **Interview / ask_user** (Phase C) — let the bot interview Lucas mid-task (essential for plan
      mode, useful elsewhere): agent questions surface as Telegram prompts/inline buttons, answers flow
      back into the running turn. (linuz90's `ask_user` MCP pattern — see [[reference_linuz90_bot]].)
      Depends on the live-feedback plumbing above.

### Telegram's rich text editor — assessed 2026-07-27, mostly NOT actionable
Lucas asked whether the new editor
([blog](https://telegram.org/blog/communities-editor-invisible-messages/pt-br)) lets us format
better: *"pelo visto tem headers. será que tabelas?"*. It announces "um editor de texto avançado
com suporte para títulos, tabelas, listas, citações e blocos de código".

**Checked against the API rather than the blog.** PTB 22.8 implements **Bot API 10.0**, whose
entity list is `BOLD, ITALIC, CODE, PRE, BLOCKQUOTE, EXPANDABLE_BLOCKQUOTE, SPOILER, UNDERLINE,
STRIKETHROUGH, TEXT_LINK, …` — **no `HEADING`, no `TABLE`.** The editor is a *client-side
composer* for humans typing in the app; it is not new surface a bot can send. So headings stay
bold-caps (AD-14) and **AD-18's pipe-tables-as-row-blocks remains correct, not a workaround**.
Nothing to do. Re-check if a future Bot API adds the entities.

- [ ] **Worth taking, and available today: `<blockquote expandable>`** (`EXPANDABLE_BLOCKQUOTE`).
      Collapses a long passage behind a "show more" the reader opens on demand. It is the one
      genuinely new-to-us lever the assessment turned up, and it fits the long-answer problem F5
      attacked from the other side — candidate for the *tail* of a long answer, or for the
      transcript echo of a long voice note. Not scheduled; it interacts with AD-23's splitting,
      so decide it after F4 lands rather than tangling two shape changes at once.

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
