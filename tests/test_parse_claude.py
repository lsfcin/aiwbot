# test_parse_claude.py — free unit test: claude fixture -> normalized AgentEvents satisfy the contract.
import pathlib
from backend.claude import parse_events
from backend.base import check_contract

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
