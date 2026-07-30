# aiwbot — Roadmap

## Context
Provider-agnostic rebuild of the workspace Telegram bot. The old bot (core/tools/telegram_daemon.py)
shells `claude -p` per message (fork/divergence). Official Anthropic Remote Control + Channels solve
sync but lock us 100% into Claude Code — against the provider-agnostic principle. Direction: streaming,
single-lineage, with a swappable backend seam (linuz90's architecture, rebuilt in Python). Providers
become interchangeable data. Full design + research: brain/goals/workspace-os.md.

Design of everything already shipped lives in [SPECS.md](SPECS.md) (AD-1…AD-31); the P2/P3 plans
in [ROADMAP-p2.md](ROADMAP-p2.md) / [ROADMAP-p3.md](ROADMAP-p3.md).

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

Earlier P-numbers keep their names so old notes resolve; their design is SPECS AD-10…AD-17.

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

**Live now:** `"stream": "true"` in `~/.config/aiwbot/config.json` defaults; ask is on by default.
Rollbacks, least drastic first: `"ask": "false"` + restart (turns invoked exactly as in Stage 3) →
`painter.STREAM_SEAL = False` (one freezing bubble, live text kept) → `"stream": "false"` + restart
(back to Stage 1). None of them is a code change.

| Stage | Goal | Checkpoint |
|---|---|---|
| **0** ✔ | split `bot.py` → `turnrun.py`, zero behaviour change | everything looks exactly as before |
| **1** ✔ | streaming seam in the backend, still batch-delivered | log shows frames ticking; Telegram identical |
| **2** ✔ | live bubble: throttled painter, pin held below | text grows ~every 3 s, footer+keyboard at the end |
| **3** ✔ | seal bubbles mid-stream (full AD-23 under streaming) | confirmed in chat 2026-07-28 |
| **4** ✔ | `ask_user` MCP transport, probe-gated | confirmed in chat 2026-07-29 — a real interview ran |
| **5** | `ask_user` in anger, close F4 | a task that matters, away from the PC (below) |

Key risks pre-empted: 64 KB subprocess stream limit (`limit=1<<20`); stderr pipe fills and hangs the
child (sibling drain task); occupancy read before the transcript flushes would silently regress b3
(`await proc.wait()` before yielding the result event); 429 pile-up (in-flight guard that *drops*
rather than queues, plus self-tuning backoff); `bot.py` 198/200 and `claude.py` 194/200 both split
**before** gaining code.

The measured CLI facts Stage 5 still needs: the 60 s tool timeout is lifted by `MCP_TOOL_TIMEOUT`,
`initialize` repeats, and plan mode refuses MCP. Design: SPECS AD-26…AD-30.

**Plan mode: settled as option A** (2026-07-29) — ask works in build mode only, the bot coerces every
turn to build, and the panel no longer offers the choice (AD-28). Option B, re-implementing
`mode=plan` as `bypassPermissions --tools "Read,Grep,Glob"`, is verified to work and deliberately not
taken: it changes what a mode Lucas uses daily means. Revisit only if a future CLI lifts the block.

### F4 Stage 5 — the last one: `ask_user` in anger
Not a demo. A genuinely underspecified task handed over while away from the PC, letting the agent
interview its way to something usable. What it tests is judgement rather than plumbing: whether the
agent asks at the *right* moments, whether it asks too much or too little, whether a 55-minute wait
behaves when the answer takes twenty, and whether a long interview leaves the chat readable. Closing
this closes F4.

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

### opencode parity — audited AND closed 2026-07-29
Asked directly ("is it properly wired to opencode, including the interview part?"), so the audit
answered from the code rather than from what the seam promises. Everything frontend-side was already
genuinely provider-agnostic: the painter, segments, counters, the transcript lead, pacing, the panel,
`guarded`, the voice feedback. Three gaps were real; all three are closed, each measured live before
it was written (SPECS AD-31). Cost of the whole thing: ~$0.15 in probes, live checks and one smoke.

- [x] **`ask_user` works on opencode.** It was claude-only because `OpencodeBackend` never overrode
      `supports_ask`. The probe overturned three of the audit's own guesses: there is **no
      `--mcp-config` flag at all** (so no temp file either — the config rides in
      `OPENCODE_CONFIG_CONTENT`), the tool call dies at **60 s with no env var to lift it** (the
      per-server `timeout` does), and `opencode mcp add` writes the USER's global config. `askserver`
      needed no behaviour change, exactly as predicted; the **seam** did, twice:
      `TurnOptions.mcp_config` (claude's JSON under an agnostic name) became `ask_url`, and
      `env()` became `env(options)` because opencode's config has no flag to ride on and a
      backend-held turn would break the moment two turns overlap. Verified live end to end through
      the REAL `askserver`: question at 10.8 s carrying both options, answer held **65 s — past the
      old ceiling — and the turn's final text was the answer**.
- [x] **The retry set now speaks both providers.** `transient` matched `529` / `overloaded` / `rate
      limit` / `timed out`, and opencode's real overload text (captured live for b2) is
      `ResourceExhausted: Worker local total request limit reached (48/48)` — none of them, so the
      retry was claude-only *in practice*. Its vocabulary is in, with a free test that runs the
      whole path (`error` line → `DispatchError` → `transient`) rather than the marker alone.
- [x] **opencode streaming has now run live, and it is COARSE.** `LineStream` works, but the grain
      is one text part **per step**, never per token: measured arrivals at 11.8 s / 15.5 s / 35.0 s
      of one turn, and a short single-step answer arrives as exactly ONE event at the end. So a
      streamed opencode turn grows in bubbles-per-step where a claude turn grows continuously —
      worth knowing before promising Lucas the same liveness on both. Nothing to fix: the throttle,
      sealing and pacing all treat whole segments correctly (`partial=False`), which is why the
      parser needed no work.
- [x] **Its `plan` agent stays unreachable from the bot — decided, not merely unbuilt** (Lucas,
      2026-07-29: *leave it global*). AD-28 coerces every turn to build for claude's sake, and
      **measured the same day, `opencode run --agent plan` called the ask tool and completed the
      round trip** — so the coercion is claude's constraint applied to everyone, and that is the
      accepted price: one meaning of `mode` across providers, and the panel level AD-28 deleted
      stays deleted. Revisit only if planning from the phone becomes something he actually wants.

#### What closing it changed, and what is still owed
The seam moved twice (`ask_url`, `env(options)`), `askserver` kept its behaviour and gave up only
claude's JSON wrapper, and five free tests landed in `tests/test_f7_opencode_ask.py`:
374 → 378 green with b4's spec. The paid side ran too — `make smoke` ALL PASS on both providers,
plus the streamed and interviewed opencode turns above.

Still owed, and the reason this is not signed off:
- [ ] **The interviewed turn has not been seen IN TELEGRAM.** It was verified through the real
      `askserver` from a script, which proves the transport but not the shape — and per AD-30 two
      bugs this session passed every assertion in their own file and were caught only by reading
      the bubbles. **The daemon is still running the old code**: picking this up needs a restart,
      which kills whatever conversation Lucas has open, so it waits for his word.
- [ ] **b4 is fixed in the repo, not in the process.** Every opencode turn from the live daemon is
      still being filed under `/home/lucas` until the same restart.

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
All three closed by P3. Kept as the record of what the audit found:
long answers could vanish entirely (blind HTML chunking), `/resume N` made one numeral name two
different sessions across pages, and anchor messages carried no mode toggle. Future audits log here
first, then move to BUGS.md with a `bN` id if they survive the round they were found in.

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
- [~] **`backend/opencode.py` is at 188/200** after the ask config landed, and `claude.py` at 176.
      Both warn, neither blocks. The seam the next touch should cut along is already visible: the
      **config/env** half (`_ask_config`, `env`, `supports_ask`, the timeout) is a different
      responsibility from the **parsing** half (`parse_events`, `LineStream`, `_line_to_event`), and
      claude already splits exactly that way (`claudeparse.py`). Do it when something needs adding,
      not now — an empty split is churn.
- [x] **`bot.py`'s size** — resolved: F4 split it into `turnrun.py`, and `painter.py`'s three later
      breaches went to `cadence.py` / `anchor.py` / `bubbles.py` / `landing.py`. Original note:
      **`bot.py` was at 198 LOC** (200 is the hard gate) after F3c's startup warm and the voice
      echo change — two lines of headroom left, so the next touch pays for the split. F4 puts
      streaming into exactly this file, so it *will* breach. Split when F4 starts, not now — the
      seam F4 introduces is what should decide where the cut goes.

## Rejected
Tried or measured, then dropped — recorded so a dead idea does not resurface looking new.
- **`concurrent_updates(True)`** — overlaps separate taps but does nothing for a single tap's
  latency (the actual complaint), while widening the race on `config.json`'s non-atomic write.
  The floor is one round trip (~222 ms); no trick beats it, because a Telegram client renders an
  inline keyboard purely from server state — no optimistic update, no local echo.
- **Forcing IPv4 to Telegram** — measured *slower* than the IPv6 default (203 vs 191 ms median).
- **A fixed 5-column panel grid** (padded with invisible cells for squareness) — 5 columns meant
  ~8-char labels and model ids stopped being distinguishable. Positional grid ≤4/row instead (AD-13).
- **Scrolling/marquee button text** — a label is static; animating costs one
  `editMessageReplyMarkup` per frame at ~1.5 s each → sub-1 fps, and flood control. The only richer
  Telegram component is a Web App webview needing an HTTPS page — revisit only if buttons stop
  being enough.
- **Telegram's rich text editor as new bot surface** — see the assessment above: client-side
  composer only, no `HEADING`/`TABLE` entity in Bot API 10.0.

## Verification
- Free (every change): `make test`. Live milestone (~$0.20): `make smoke`.
