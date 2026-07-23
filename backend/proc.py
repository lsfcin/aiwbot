# proc.py — subprocess driver + run-result → events handling (shared by all CLI backends).
from __future__ import annotations
import asyncio
import os
from typing import Callable
from .base import AgentEvent


async def run_capture(args: list[str], cwd: str, extra_env: dict | None = None) -> tuple[str, str, int]:
    """Run args in cwd, wait, return (stdout, stderr, returncode). communicate() drains pipes safely.
    extra_env overlays the daemon's environment (backends use it for provider-specific knobs)."""
    pipe = asyncio.subprocess.PIPE
    env = None
    if extra_env:
        env = dict(os.environ)
        env.update(extra_env)
    proc = await asyncio.create_subprocess_exec(*args, cwd=cwd, stdout=pipe, stderr=pipe, env=env)
    out_bytes, err_bytes = await proc.communicate()
    code = proc.returncode
    out = out_bytes.decode()
    err = err_bytes.decode()
    return out, err, code


def events_from_run(out: str, err: str, code: int, parse: Callable[[str], list[AgentEvent]]) -> list[AgentEvent]:
    """Hard-fail (nonzero + empty stdout) -> one error event; otherwise delegate to the backend parser."""
    failed = code != 0 and not out.strip()
    events: list[AgentEvent] = []
    if failed:
        tail = err[-500:]
        events.append(AgentEvent(kind="error", text=tail))
    else:
        events = parse(out)
    return events
