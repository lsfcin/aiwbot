# opencode.py — OpencodeBackend: normalizes `opencode run --format json` (JSONL stream).
from __future__ import annotations
import json
from . import binaries, catalog, ocstore
from .base import AgentEvent, TurnOptions, add_flag, try_json
from .caps import Capabilities
from .cli import CliBackend

_MODES = ("build", "plan")
# How much of an unrecognized error line to quote back. Enough to identify the shape when a
# provider invents a new one, short enough not to dump a payload into a chat bubble.
_ERROR_CHARS = 300


def _row_to_item(row: tuple) -> dict:
    """Session row -> picker index entry. `agent` and `model` ride in the row itself, so mode
    and model cost no join; preview and context % need one and arrive via session_detail."""
    model = ocstore.model_of(row[4])
    window = catalog.context_window(model) if model else None
    updated = row[2] / 1000.0
    return {"session_id": row[0], "title": row[1], "updated_at": updated,
            "mode": row[3], "model": model, "context_window": window}


def _error_text(obj: dict) -> str:
    """Captured live from the CLI (b2): an error line is
    `{"type":"error","sessionID":…,"error":{"name":"UnknownError","data":{"message":…,"ref":…}}}`.
    The nested message is the part worth reading — the outer name stays `UnknownError` even when
    the cause is perfectly knowable ("ResourceExhausted: Worker local total request limit reached
    (48/48)"). Fall back to the name, then the raw object, so no shape can yield an empty reason."""
    error = obj.get("error")
    text = ""
    if isinstance(error, dict):
        data = error.get("data")
        if isinstance(data, dict):
            text = data.get("message") or ""
        if not text:
            text = error.get("name") or ""
    if not text:
        dumped = json.dumps(obj)
        text = dumped[:_ERROR_CHARS]
    return text


def _line_to_event(obj: dict) -> AgentEvent | None:
    """opencode JSONL: type=text carries part.text, type=step_finish carries part.cost,
    type=error carries the reason a turn produced no text at all."""
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
    elif kind == "error":
        text = _error_text(obj)
        result = AgentEvent(kind="error", text=text, session_id=sid)
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
        `--agent build|plan` are both primary agents, so mode maps one-for-one with claude's
        --permission-mode (AD-10 corrected the old "opencode has no plan/build" claim).
        Effort maps to --variant, whose vocabulary is per-model — see catalog.efforts."""
        agent = "plan" if options.mode == "plan" else "build"
        binary = binaries.resolve("opencode")
        args = [binary, "run", prompt, "--format", "json"]
        add_flag(args, "--agent", agent)
        add_flag(args, "-m", options.model)
        add_flag(args, "--variant", options.effort)
        if session_id:
            add_flag(args, "-s", session_id)
        else:
            add_flag(args, "--title", options.title)
        return args

    def parse(self, stdout: str) -> list[AgentEvent]:
        return parse_events(stdout)

    def capabilities(self) -> Capabilities:
        """478 configured models: `favourites` is the cheap-first shortlist and `groups` is the
        provider drill-down behind it — a flat keyboard is not an option here (SPECS AD-11)."""
        return Capabilities(modes=list(_MODES), favourites=catalog.favourites(),
                            groups=catalog.groups())

    def efforts(self, model: str | None = None) -> list[str]:
        """Per-model, from models.json. Empty for the toggle/budget_tokens shapes."""
        values: list[str] = []
        if model:
            values = catalog.efforts(model)
        return values

    def list_sessions(self, cwd: str) -> list[dict]:
        """Read top-level sessions for cwd from opencode's sqlite store. Mirrors the claude
        backend so the picker unifies both — same fields, same 3-line entry."""
        rows = ocstore.session_rows(cwd)
        return [_row_to_item(row) for row in rows]

    def last_response(self, session_id: str, cwd: str) -> str:
        """Last assistant answer, for the /resume re-anchor body."""
        text, _ = ocstore.last_turn(session_id)
        return text

    def occupancy(self, session_id: str, cwd: str) -> int | None:
        """Per-message occupancy from the store — the same number the /resume list shows, so a
        live turn and a listed session report context the same way (b3). The JSONL stream itself
        carries no usage breakdown, so before this an opencode answer showed no % at all."""
        _text, used = ocstore.last_turn(session_id)
        return used

    def session_detail(self, session_id: str, cwd: str) -> dict:
        """The bits that cost a query: answer preview + context occupancy. Called for the
        page being rendered, not for all 59 listed sessions."""
        text, used = ocstore.last_turn(session_id)
        return {"preview": text, "context_used": used}
