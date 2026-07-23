# dispatch.py — one call site that drains any AgentBackend.send() into a single reply.
from __future__ import annotations
from dataclasses import dataclass
from backend import get_backend, TurnOptions
from backend.base import check_contract


@dataclass
class TurnResult:
    text: str
    session_id: str
    cost_usd: float | None
    model: str | None = None
    context_used: int | None = None
    context_window: int | None = None


class DispatchError(Exception):
    pass


def events_to_result(events: list) -> TurnResult:
    """Pure (free to unit-test): AgentEvent list -> single reply, or raises DispatchError."""
    errors = [e for e in events if e.kind == "error"]
    if errors:
        raise DispatchError(errors[-1].text)
    ok, reason = check_contract(events)
    if not ok:
        raise DispatchError(reason)
    texts = [e.text for e in events if e.kind == "text"]
    result = [e for e in events if e.kind == "result"][-1]
    body = "\n".join(texts)
    return TurnResult(text=body, session_id=result.session_id, cost_usd=result.cost_usd,
                      model=result.model, context_used=result.context_used,
                      context_window=result.context_window)


async def turn(prompt: str, *, session_id: str | None, backend_name: str, cwd: str,
               options: TurnOptions = TurnOptions()) -> TurnResult:
    backend = get_backend(backend_name)
    stream = backend.send(prompt, session_id=session_id, cwd=cwd, options=options)
    events = [event async for event in stream]
    return events_to_result(events)
