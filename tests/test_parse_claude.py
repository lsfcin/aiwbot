# test_parse_claude.py — free unit test: claude fixture -> normalized AgentEvents satisfy the contract.
import pathlib
from backend.claude import parse_events, ClaudeBackend
from backend.base import check_contract, TurnOptions

_FIX = pathlib.Path(__file__).parent / "fixtures" / "claude_pong.json"


def _events():
    raw = _FIX.read_text()
    events = parse_events(raw)
    return events


def test_claude_has_text_and_result():
    events = _events()
    kinds = [e.kind for e in events]
    assert "text" in kinds
    assert "result" in kinds


def test_claude_text_and_session():
    events = _events()
    texts = [e for e in events if e.kind == "text"]
    first = texts[0]
    assert first.text == "PONG"
    assert first.session_id == "abc12345-6789-42ab-9cde-0123456789ab"


def test_claude_contract():
    events = _events()
    ok, reason = check_contract(events)
    assert ok, reason


def test_resume_is_single_lineage_no_fork():
    # AD-3 (revised): plain --resume keeps one lineage; --fork-session would mint a new id
    # per turn and pile up cumulative VSCode sessions. Lock the no-fork decision.
    backend = ClaudeBackend()
    args = backend.build_args("hi", "some-session-id", TurnOptions())
    assert "--resume" in args
    assert "--fork-session" not in args


def _perm_value(args):
    idx = args.index("--permission-mode")
    return args[idx + 1]


def test_build_args_build_mode_keeps_bypass():
    backend = ClaudeBackend()
    args = backend.build_args("hi", None, TurnOptions(mode="build"))
    assert _perm_value(args) == "bypassPermissions"


def test_build_args_plan_mode_sets_permission_plan():
    backend = ClaudeBackend()
    args = backend.build_args("hi", None, TurnOptions(mode="plan"))
    assert _perm_value(args) == "plan"
