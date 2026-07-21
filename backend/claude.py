# claude.py — ClaudeBackend: normalizes `claude -p --output-format json` (single result object).
from __future__ import annotations
import pathlib
import shutil
from .base import AgentEvent, try_json
from .cli import CliBackend

_EXT_GLOB = ".vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude"


def _claude_bin() -> str:
    """Resolve the claude binary: PATH override first, else the bundled VSCode-extension build."""
    override = shutil.which("claude")
    result = override
    if not override:
        home = pathlib.Path.home()
        raw = home.glob(_EXT_GLOB)
        candidates = sorted(raw)
        if not candidates:
            raise RuntimeError("claude binary not found (PATH + VSCode extension dir)")
        result = str(candidates[-1])
    return result


def _last_json_object(stdout: str) -> dict | None:
    """claude -p --output-format json prints one result object; scan from the end for it."""
    lines = stdout.splitlines()
    found: dict | None = None
    for line in reversed(lines):
        stripped = line.strip()
        if stripped.startswith("{"):
            found = try_json(stripped)
        if found is not None:
            break
    return found


def _model_of(obj: dict) -> str | None:
    """claude reports the model as the key of `modelUsage` (e.g. claude-sonnet-5)."""
    usage = obj.get("modelUsage") or {}
    keys = list(usage)
    result = keys[0] if keys else None
    return result


def _object_to_events(obj: dict) -> list[AgentEvent]:
    sid = obj.get("session_id")
    is_error = obj.get("is_error")
    events: list[AgentEvent] = []
    if is_error:
        text = obj.get("result", "")
        events.append(AgentEvent(kind="error", text=text, session_id=sid))
    else:
        text = obj.get("result", "")
        cost = obj.get("total_cost_usd")
        model = _model_of(obj)
        events.append(AgentEvent(kind="text", text=text, session_id=sid))
        events.append(AgentEvent(kind="result", session_id=sid, cost_usd=cost, model=model))
    return events


def parse_events(stdout: str) -> list[AgentEvent]:
    """Pure normalizer (free to unit-test): claude result object -> AgentEvents."""
    obj = _last_json_object(stdout)
    events: list[AgentEvent] = []
    if obj is None:
        events.append(AgentEvent(kind="error", text="no JSON result in claude output"))
    else:
        events = _object_to_events(obj)
    return events


class ClaudeBackend(CliBackend):
    name = "claude"

    def build_args(self, prompt: str, session_id: str | None) -> list[str]:
        """Plain --resume, no fork: keeps one lineage (same id, same transcript) per AD-3.
        Fork was only needed in the old bot's --bg era, where a live agent locked the id."""
        binary = _claude_bin()
        args = [binary, "-p", "--output-format", "json", "--permission-mode", "bypassPermissions"]
        if session_id:
            args.append("--resume")
            args.append(session_id)
        args.append(prompt)
        return args

    def parse(self, stdout: str) -> list[AgentEvent]:
        return parse_events(stdout)
