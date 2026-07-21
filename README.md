# aiwbot
> Provider-agnostic bot: drive swappable coding agents (claude · opencode · copilot) from chat.

## What it does
One `AgentBackend` interface normalizes every coding-agent CLI into a stream of `AgentEvent`s, so the
frontend never knows which provider runs underneath — provider is data, not code. No lock-in to any
single agent. Reuses the workspace Telegram bot's plumbing for capture/allowlist/formatting.

## Architecture
- `backend/base.py` — `AgentEvent`, `AgentBackend` protocol, `check_contract`, `try_json`.
- `backend/cli.py` — `CliBackend`: the one subprocess-driven `send()` loop.
- `backend/claude.py` / `backend/opencode.py` — subclasses: `build_args` + pure `parse_events`.
- `backend/__init__.py` — facade + `get_backend(name)` registry.
- `proto.py` — live smoke harness. `tests/` — free fixture-driven parser tests.

## Quickstart
```bash
make test    # free: fixture-driven parser tests, no network/cost
make smoke   # live: run a real prompt through each backend (~$0.20)
```

## Status
Phase A complete: seam proven live against claude + opencode (single-lineage resume). Phase B
(Telegram frontend, `frontend/`) coded + free-tested, live smoke pending. Full plan → ROADMAP.md.

## License
TBD

---
[CONTEXT.md](CONTEXT.md) · [SPECS.md](SPECS.md) · [ROADMAP.md](ROADMAP.md)
