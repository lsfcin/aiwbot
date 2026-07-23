# claude.py — ClaudeBackend: normalizes `claude -p --output-format json` (single result object).
from __future__ import annotations
import pathlib
from . import binaries, transcript
from .base import AgentEvent, TurnOptions, add_flag, try_json
from .caps import Capabilities
from .cli import CliBackend

_PROJECTS = ".claude/projects"
# The one entrypoint value the native picker lists. "cli" is rejected (falls back to sdk-cli).
_ENTRYPOINT = "claude-vscode"
_MODES = ("build", "plan")
# `--model` takes an alias for the latest model of a family, or a full id. Aliases age better
# than ids, so the picker offers those; a full id still works if it is ever set by hand.
_MODELS = ("opus", "sonnet", "fable")
# One ladder for every claude model — verified in `claude --help` 2026-07-23.
_EFFORTS = ("low", "medium", "high", "xhigh", "max")


def _project_dir(cwd: str) -> pathlib.Path:
    """Claude Code stores a cwd's transcripts under ~/.claude/projects/<cwd, / -> ->."""
    slug = cwd.replace("/", "-")
    return pathlib.Path.home() / _PROJECTS / slug


def _opening_prompt(path: pathlib.Path) -> str:
    """First `last-prompt` line = the session's opening prompt (near the top -> cheap scan)."""
    title = ""
    with path.open() as handle:
        for line in handle:
            if '"type":"last-prompt"' not in line:
                continue
            obj = try_json(line.strip())
            if obj is not None:
                title = obj.get("lastPrompt") or ""
            break
    return title


def _session_item(path: pathlib.Path) -> dict:
    sid = path.stem
    lines = transcript.tail_lines(path)
    title = transcript.latest_ai_title(lines)
    if not title:
        title = _opening_prompt(path)
    preview = transcript.last_response_text(lines)
    model = transcript.last_model(lines)
    used = transcript.last_context_used(lines)
    updated = path.stat().st_mtime
    return {"session_id": sid, "title": title, "updated_at": updated,
            "preview": preview, "model": model, "context_used": used}


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


_CONTEXT_FIELDS = ("inputTokens", "cacheReadInputTokens", "cacheCreationInputTokens")


def _context_of(obj: dict, model: str | None) -> tuple[int | None, int | None]:
    """Context occupancy after the turn: modelUsage[model] carries both the token
    breakdown and the window, so the % costs nothing extra to report."""
    usage = obj.get("modelUsage") or {}
    entry = usage.get(model or "") or {}
    window = entry.get("contextWindow")
    used = None
    if entry:
        counts = [entry.get(f) or 0 for f in _CONTEXT_FIELDS]
        used = sum(counts)
    return used, window


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
        used, window = _context_of(obj, model)
        events.append(AgentEvent(kind="text", text=text, session_id=sid))
        events.append(AgentEvent(kind="result", session_id=sid, cost_usd=cost, model=model,
                                 context_used=used, context_window=window))
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

    def build_args(self, prompt: str, session_id: str | None, options: TurnOptions) -> list[str]:
        """Plain --resume, no fork: keeps one lineage (same id, same transcript) per AD-3.
        Fork was only needed in the old bot's --bg era, where a live agent locked the id.
        mode=plan -> --permission-mode plan (agent plans, no edits); build -> bypassPermissions."""
        binary = binaries.resolve("claude")
        perm = "plan" if options.mode == "plan" else "bypassPermissions"
        args = [binary, "-p", "--output-format", "json", "--permission-mode", perm]
        add_flag(args, "--model", options.model)
        add_flag(args, "--effort", options.effort)
        if session_id:
            add_flag(args, "--resume", session_id)
        else:
            add_flag(args, "--name", options.title)
        args.append(prompt)
        return args

    def capabilities(self) -> Capabilities:
        """A handful of aliases — small enough that `favourites` IS the whole catalogue and
        the drill-down never opens. The opposite of opencode's 478 (SPECS AD-11)."""
        models = list(_MODELS)
        return Capabilities(modes=list(_MODES), favourites=models, groups={"claude": models})

    def efforts(self, model: str | None = None) -> list[str]:
        """Same ladder whatever the model, so the argument is accepted and ignored."""
        return list(_EFFORTS)

    def last_response(self, session_id: str, cwd: str) -> str:
        """Full text of the session's last answer, read from the transcript — lets /resume
        re-anchor a session by showing where it left off, not just its title."""
        directory = _project_dir(cwd)
        path = directory / f"{session_id}.jsonl"
        text = ""
        if path.is_file():
            lines = transcript.tail_lines(path)
            text = transcript.last_response_text(lines)
        return text

    def env(self) -> dict | None:
        """AD-8 (revised): Claude Code's native picker hides sessions whose ORIGINATING
        entrypoint is `sdk-cli`, which is what a bare headless `-p` records. The entrypoint
        comes from this env var, not from the flags — setting it makes bot-created sessions
        show up in the VSCode/terminal picker like any other. Verified live 2026-07-23."""
        return {"CLAUDE_CODE_ENTRYPOINT": _ENTRYPOINT}

    def parse(self, stdout: str) -> list[AgentEvent]:
        return parse_events(stdout)

    def list_sessions(self, cwd: str) -> list[dict]:
        """Read the canonical store (~/.claude/projects/<cwd>/*.jsonl) so the picker shows
        every resumable session for cwd — including ones started in VSCode, not just the bot's."""
        directory = _project_dir(cwd)
        items: list[dict] = []
        if directory.is_dir():
            for path in directory.glob("*.jsonl"):
                item = _session_item(path)
                items.append(item)
        return items
