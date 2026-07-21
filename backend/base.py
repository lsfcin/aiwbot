# base.py — the provider-agnostic seam: AgentEvent + AgentBackend contract + shared primitives.
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import AsyncIterator, Literal, Protocol, runtime_checkable

EventKind = Literal["text", "thinking", "tool", "result", "error"]


@dataclass
class AgentEvent:
    kind: EventKind
    text: str = ""
    tool: str | None = None
    session_id: str | None = None
    cost_usd: float | None = None
    model: str | None = None


@runtime_checkable
class AgentBackend(Protocol):
    name: str

    def send(self, prompt: str, *, session_id: str | None, cwd: str) -> AsyncIterator[AgentEvent]:
        ...


def try_json(text: str) -> dict | None:
    """Parse one line as a JSON object, or None if it isn't valid JSON / isn't an object."""
    result: dict | None = None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        result = parsed
    return result


def check_contract(events: list[AgentEvent]) -> tuple[bool, str]:
    """Minimum backend contract: >=1 text event AND a terminal result carrying a session_id."""
    texts = [e for e in events if e.kind == "text"]
    results = [e for e in events if e.kind == "result"]
    ok = True
    reason = "ok"
    if not texts:
        ok = False
        reason = "no text event"
    elif not results:
        ok = False
        reason = "no result event"
    else:
        last = results[-1]
        if not last.session_id:
            ok = False
            reason = "result missing session_id"
    return ok, reason
