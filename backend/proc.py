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


_TAIL_CHARS = 500
_SILENT = ("the CLI exited {code} and produced output this backend does not recognize. "
           "Raw tail:\n{tail}")


def _tail(out: str, err: str) -> str:
    """Whatever the CLI actually said. stdout first — a CLI that streamed something we failed
    to parse put the reason there; stderr is the fallback for one that never streamed at all."""
    source = out.strip() or err.strip()
    return source[-_TAIL_CHARS:]


def events_from_run(out: str, err: str, code: int, parse: Callable[[str], list[AgentEvent]]) -> list[AgentEvent]:
    """Hard-fail (nonzero + empty stdout) -> one error event; otherwise delegate to the backend
    parser. A parser that recognizes NOTHING is also a failure: b2 had opencode exit 0 while
    streaming an error shape no `_line_to_event` branch matched, so zero events reached the
    frontend and `check_contract` reported the useless "no text event" instead of the real
    reason. Quoting the raw tail means the next unrecognized shape names itself."""
    failed = code != 0 and not out.strip()
    events: list[AgentEvent] = []
    if failed:
        tail = _tail(out, err)
        events.append(AgentEvent(kind="error", text=tail))
    else:
        events = parse(out)
    if not events:
        tail = _tail(out, err)
        text = _SILENT.format(code=code, tail=tail)
        events = [AgentEvent(kind="error", text=text)]
    return events
