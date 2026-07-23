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
    # Context-window occupancy after this turn. Providers that don't report it leave both None.
    context_used: int | None = None
    context_window: int | None = None


@dataclass
class TurnOptions:
    """Per-turn knobs threaded from the frontend to a backend's build_args.
    Provider-agnostic: each backend maps what it can and ignores the rest.
    mode ∈ {build, plan}. title names a new session (claude --name -> visible in its /resume).
    Room to grow (model, effort) for the next tier."""
    mode: str = "build"
    title: str | None = None


@runtime_checkable
class AgentBackend(Protocol):
    name: str

    def send(self, prompt: str, *, session_id: str | None, cwd: str,
             options: TurnOptions = TurnOptions()) -> AsyncIterator[AgentEvent]:
        ...

    def list_sessions(self, cwd: str) -> list[dict]:
        """Resumable sessions for cwd from the provider's own store, newest-first-agnostic.
        Each item: {session_id, title, updated_at}. Lets the frontend picker show sessions
        started anywhere (e.g. VSCode), not just ones the bot created."""
        ...

    def last_response(self, session_id: str, cwd: str) -> str:
        """Full text of that session's last agent answer, or "" if the provider can't say."""
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
