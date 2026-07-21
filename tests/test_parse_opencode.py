# test_parse_opencode.py — free unit test: opencode JSONL fixture -> AgentEvents satisfy the contract.
import pathlib
from backend.opencode import parse_events
from backend.base import check_contract

_FIX = pathlib.Path(__file__).parent / "fixtures" / "opencode_pong.jsonl"


def _events():
    raw = _FIX.read_text()
    events = parse_events(raw)
    return events


def test_opencode_has_text_and_result():
    events = _events()
    kinds = [e.kind for e in events]
    assert "text" in kinds
    assert "result" in kinds


def test_opencode_text_and_session():
    events = _events()
    texts = [e for e in events if e.kind == "text"]
    first = texts[0]
    assert first.text == "PONG"
    assert first.session_id is not None


def test_opencode_contract():
    events = _events()
    ok, reason = check_contract(events)
    assert ok, reason
