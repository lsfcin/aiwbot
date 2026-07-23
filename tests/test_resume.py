# test_resume.py — free unit test: /resume picker list/label/pagination assembly.
import time
from frontend.resume import _entry_line, _list_text, _header, _parse_arg, _meta, _clip, _keyboard

_NOW = time.time()


def test_meta_line_order_is_provider_model_mode_context_when():
    item = {"backend": "claude", "updated_at": _NOW, "mode": "plan", "model": "claude-sonnet-5",
            "context_used": 320_000, "context_window": 1_000_000}
    assert _meta(item) == "claude · sonnet · plan · 32% · agora"


def test_meta_line_omits_missing_mode_model_and_context():
    item = {"backend": "opencode", "updated_at": _NOW}
    assert _meta(item) == "opencode · agora"


def test_meta_line_omits_context_without_known_window():
    item = {"backend": "claude", "updated_at": _NOW, "context_used": 320_000, "context_window": None}
    assert _meta(item) == "claude · agora"


def test_entry_line_three_lines_with_preview():
    item = {"title": "hello world session", "preview": "faz isso e a resposta fica pronta agora",
            "backend": "claude", "updated_at": _NOW, "mode": "plan", "model": "claude-sonnet-5"}
    line = _entry_line(1, item)
    expected = ("1. HELLO WORLD SESSION\n"
                "faz isso e a resposta fica pronta agora\n"
                "claude · sonnet · plan · agora")
    assert line == expected


def test_entry_line_omits_preview_when_absent():
    item = {"title": "hello world session", "preview": None, "backend": "claude", "updated_at": _NOW}
    line = _entry_line(2, item)
    assert line == "2. HELLO WORLD SESSION\nclaude · agora"


def test_title_caps_at_five_words():
    item = {"title": "one two three four five six seven eight", "preview": None,
            "backend": "claude", "updated_at": _NOW}
    line = _entry_line(1, item)
    assert line.startswith("1. ONE TWO THREE FOUR FIVE\n")


def test_list_text_blank_line_between_entries():
    items = [{"title": "a", "preview": None, "backend": "claude", "updated_at": _NOW},
              {"title": "b", "preview": None, "backend": "opencode", "updated_at": _NOW}]
    text = _list_text(items)
    assert text == "1. A\nclaude · agora\n\n2. B\nopencode · agora"


def test_clip_marks_truncation():
    clipped = _clip("x" * 5000, 100)
    assert clipped.endswith("[…]")
    assert len(clipped) == 104


def test_header_hints_full_count_command_when_more_exist():
    assert _header(12, 5, "") == "Sessões recentes — 5 de 12 · /resume 12 pra ver todas"


def test_header_no_hint_when_all_shown():
    assert _header(3, 3, "") == "Sessões recentes — 3 de 3"


def test_parse_arg_digit_is_count():
    assert _parse_arg("10") == ("", 10)


def test_parse_arg_text_is_query():
    assert _parse_arg("bugfix") == ("bugfix", 5)


def test_keyboard_is_single_row_of_numerals():
    items = [{"session_id": "sid-a", "title": "a", "backend": "claude", "updated_at": _NOW},
              {"session_id": "sid-b", "title": "b", "backend": "opencode", "updated_at": _NOW}]
    markup = _keyboard(items)
    row = markup.inline_keyboard[0]
    assert [b.text for b in row] == ["1", "2"]
    assert [b.callback_data for b in row] == ["resume:sid-a", "resume:sid-b"]
