# test_resume.py — free unit test: /resume picker list/label/pagination assembly.
import time
from frontend.resume import _label, _entry_line, _list_text, _header, _parse_arg, _truncate, _keyboard

_NOW = time.time()


def test_label_single_line():
    item = {"title": "hello world session", "backend": "claude", "updated_at": _NOW}
    assert _label(item) == "HELLO WORLD SESSION · agora · claude"


def test_entry_line_appends_preview_on_second_line():
    item = {"title": "hello world session", "preview": "faz isso … resposta pronta",
            "backend": "claude", "updated_at": _NOW}
    line = _entry_line(1, item)
    assert line == "1. HELLO WORLD SESSION · agora · claude\nfaz isso … resposta pronta\n"


def test_entry_line_omits_preview_when_absent():
    item = {"title": "hello world session", "preview": None, "backend": "claude", "updated_at": _NOW}
    line = _entry_line(2, item)
    assert line == "2. HELLO WORLD SESSION · agora · claude"


def test_list_text_numbers_sequentially():
    items = [{"title": "a", "backend": "claude", "updated_at": _NOW},
              {"title": "b", "backend": "opencode", "updated_at": _NOW}]
    text = _list_text(items)
    assert text.startswith("1. A · agora · claude\n2. B · agora · opencode")


def test_header_hints_full_count_command_when_more_exist():
    assert _header(12, 5, "") == "Sessões recentes — 5 de 12 · /resume 12 pra ver todas"


def test_header_no_hint_when_all_shown():
    assert _header(3, 3, "") == "Sessões recentes — 3 de 3"


def test_parse_arg_digit_is_count():
    assert _parse_arg("10") == ("", 10)


def test_parse_arg_text_is_query():
    assert _parse_arg("bugfix") == ("bugfix", 5)


def test_truncate_adds_ellipsis_over_limit():
    assert _truncate("a" * 70, 60) == "a" * 59 + ". . ."


def test_truncate_leaves_short_text_untouched():
    assert _truncate("short", 60) == "short"


def test_keyboard_is_single_row_of_numerals():
    items = [{"session_id": "sid-a", "title": "a", "backend": "claude", "updated_at": _NOW},
              {"session_id": "sid-b", "title": "b", "backend": "opencode", "updated_at": _NOW}]
    markup = _keyboard(items)
    row = markup.inline_keyboard[0]
    assert [b.text for b in row] == ["1", "2"]
    assert [b.callback_data for b in row] == ["resume:sid-a", "resume:sid-b"]
