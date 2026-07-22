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


def test_build_args_new_session_sets_name():
    backend = ClaudeBackend()
    args = backend.build_args("hi", None, TurnOptions(title="my title"))
    idx = args.index("--name")
    assert args[idx + 1] == "my title"


def test_build_args_resume_omits_name():
    backend = ClaudeBackend()
    args = backend.build_args("hi", "sid-1", TurnOptions(title="my title"))
    assert "--name" not in args


def test_build_args_new_without_title_omits_name():
    backend = ClaudeBackend()
    args = backend.build_args("hi", None, TurnOptions())
    assert "--name" not in args


def test_list_sessions_reads_store(tmp_path, monkeypatch):
    import backend.claude as C
    sid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    line = '{"type":"last-prompt","lastPrompt":"olá mundo"}\n'
    (tmp_path / f"{sid}.jsonl").write_text(line)
    monkeypatch.setattr(C, "_project_dir", lambda cwd: tmp_path)
    items = ClaudeBackend().list_sessions("/mnt/workspace")
    assert len(items) == 1
    assert items[0]["session_id"] == sid
    assert items[0]["title"] == "olá mundo"


def test_list_sessions_missing_dir_is_empty(tmp_path, monkeypatch):
    import backend.claude as C
    monkeypatch.setattr(C, "_project_dir", lambda cwd: tmp_path / "nope")
    assert ClaudeBackend().list_sessions("/x") == []
