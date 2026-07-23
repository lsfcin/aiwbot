# opencode.py — OpencodeBackend: normalizes `opencode run --format json` (JSONL stream).
from __future__ import annotations
import pathlib
import sqlite3
from .base import AgentEvent, TurnOptions, try_json
from .cli import CliBackend

_DB = ".local/share/opencode/opencode.db"
_LIST_SQL = ("SELECT id, title, time_updated FROM session "
             "WHERE directory = ? AND parent_id IS NULL")


def _db_path() -> pathlib.Path:
    return pathlib.Path.home() / _DB


def _row_to_item(row: tuple) -> dict:
    sid = row[0]
    title = row[1]
    updated = row[2] / 1000.0
    return {"session_id": sid, "title": title, "updated_at": updated}


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
        options.mode is not wired yet — but opencode DOES have the equivalent: `--agent
        build|plan` are both primary agents (verified 2026-07-23, correcting an earlier
        claim here). Mapping it belongs to the backend/model/effort tier; until then the
        run uses opencode's default agent."""
        args = ["opencode", "run", prompt, "--format", "json"]
        if session_id:
            args.append("-s")
            args.append(session_id)
        return args

    def parse(self, stdout: str) -> list[AgentEvent]:
        return parse_events(stdout)

    def list_sessions(self, cwd: str) -> list[dict]:
        """Read top-level sessions for cwd from opencode's sqlite store (session.title;
        time_updated is ms). Mirrors the claude backend so the picker unifies both."""
        db = _db_path()
        items: list[dict] = []
        if db.exists():
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            rows = con.execute(_LIST_SQL, (cwd,)).fetchall()
            con.close()
            items = [_row_to_item(row) for row in rows]
        return items
