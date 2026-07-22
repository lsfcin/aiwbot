# opencode.py — OpencodeBackend: normalizes `opencode run --format json` (JSONL stream).
from __future__ import annotations
from .base import AgentEvent, TurnOptions, try_json
from .cli import CliBackend


def _line_to_event(obj: dict) -> AgentEvent | None:
    """opencode JSONL: type=text carries part.text, type=step_finish carries part.cost."""
    kind = obj.get("type")
    part = obj.get("part", {})
    sid = obj.get("sessionID")
    result: AgentEvent | None = None
    if kind == "text":
        text = part.get("text", "")
        result = AgentEvent(kind="text", text=text, session_id=sid)
    elif kind == "step_finish":
        cost = part.get("cost")
        result = AgentEvent(kind="result", session_id=sid, cost_usd=cost)
    return result


def parse_events(stdout: str) -> list[AgentEvent]:
    """Pure normalizer (free to unit-test): opencode JSONL -> AgentEvents."""
    lines = stdout.splitlines()
    events: list[AgentEvent] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        obj = try_json(stripped)
        if obj is None:
            continue
        event = _line_to_event(obj)
        if event is not None:
            events.append(event)
    return events


class OpencodeBackend(CliBackend):
    name = "opencode"

    def build_args(self, prompt: str, session_id: str | None, options: TurnOptions) -> list[str]:
        """opencode continues the same lineage with -s <id> (no fork flag, unlike claude).
        options.mode is ignored: opencode's headless run has no plan/build equivalent (maps
        what it can, per the provider-agnostic seam)."""
        args = ["opencode", "run", prompt, "--format", "json"]
        if session_id:
            args.append("-s")
            args.append(session_id)
        return args

    def parse(self, stdout: str) -> list[AgentEvent]:
        return parse_events(stdout)
