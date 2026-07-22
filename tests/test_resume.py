# test_resume.py — free unit test: /resume picker button label assembly.
from frontend.resume import _label, _truncate


def test_label_three_lines_with_preview():
    item = {"title": "hello world session", "preview": "faz isso … resposta pronta",
            "backend": "claude", "updated_at": 0}
    label = _label(item)
    lines = label.split("\n")
    assert lines[0] == "HELLO WORLD SESSION"
    assert lines[1] == "faz isso … resposta pronta"
    assert lines[2].endswith("· claude")


def test_label_omits_preview_line_when_absent():
    item = {"title": "hello world session", "preview": None, "backend": "claude", "updated_at": 0}
    label = _label(item)
    assert len(label.split("\n")) == 2


def test_truncate_adds_ellipsis_over_limit():
    assert _truncate("a" * 50, 40) == "a" * 39 + "…"


def test_truncate_leaves_short_text_untouched():
    assert _truncate("short", 40) == "short"
