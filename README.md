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

## Operate the live bot
Runs as a systemd user service — service file at
`~/.config/systemd/user/aiwbot.service` (outside this repo), `WorkingDirectory` points here and
`ExecStart` runs `python -m frontend.bot` straight off whatever's checked out on disk. Switching
branches or pulling changes takes effect only after a restart (the running process has already
loaded the old code).

```bash
systemctl --user status  aiwbot.service   # is it up, since when, recent log tail
systemctl --user restart aiwbot.service   # pick up new code
systemctl --user stop    aiwbot.service
systemctl --user start   aiwbot.service
journalctl --user -u aiwbot.service -f    # follow logs live
```

`Restart=always` (5s backoff, capped 10 restarts/5min) — crashes self-heal. `Wants=network-online.target`
so it waits for network on boot, but the user unit itself does **not** survive a reboot without a login
session unless lingering is enabled (`loginctl enable-linger lucas`, needs sudo — not currently set).

## Status
Phase A complete: seam proven live against claude + opencode (single-lineage resume). Phase B
(Telegram frontend, `frontend/`) coded + free-tested, live smoke pending. Full plan → ROADMAP.md.

## License
TBD

---
[CONTEXT.md](CONTEXT.md) · [SPECS.md](SPECS.md) · [ROADMAP.md](ROADMAP.md)
