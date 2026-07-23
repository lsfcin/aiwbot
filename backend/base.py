# base.py — the provider-agnostic seam: AgentEvent + AgentBackend contract + shared primitives.
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import AsyncIterator, Literal, Protocol, runtime_checkable
from .caps import Capabilities

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
    model/effort are opaque strings the backend declared itself (see caps.Capabilities and
    AgentBackend.efforts) — the frontend never invents one, so no value needs translating."""
    mode: str = "build"
    title: str | None = None
    model: str | None = None
    effort: str | None = None


def add_flag(args: list[str], name: str, value: str | None) -> None:
    """Append `--name value` when value is set. Every backend builds its argv this way, so
    the guard lives here once instead of as an if/append/append triple per knob."""
    if value:
        args.append(name)
        args.append(value)


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

    def session_detail(self, session_id: str, cwd: str) -> dict:
        """Extra picker fields (preview, context_used) that cost a per-session query, so the
        frontend asks only for the page it renders. {} when list_sessions already had them."""
        ...

    def capabilities(self) -> Capabilities:
        """Modes + models this backend can be given. The frontend offers only what lands here."""
        ...

    def efforts(self, model: str | None = None) -> list[str]:
        """Effort vocabulary for a model — per-model because opencode's `--variant` values are
        (claude's `--effort low..max` is one ladder for everything). Empty = no effort knob."""
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
