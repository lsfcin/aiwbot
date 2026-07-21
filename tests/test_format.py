# test_format.py — free unit test: markdown/table -> Telegram HTML conversion.
from frontend.format import format_body, session_block, title_words


def test_plain_markdown_to_html():
    out = format_body("**bold** and `code`")
    assert out == "<b>bold</b> and <code>code</code>"


def test_pipe_table_boxed_as_pre():
    text = "| a | b |\n|---|---|\n| 1 | 2 |"
    out = format_body(text)
    assert out.startswith("<pre>")
    assert out.endswith("</pre>")
    assert "| a | b |" in out


def test_fenced_code_block_boxed_as_pre():
    out = format_body("before\n```\nraw <text>\n```\nafter")
    assert "<pre>\nraw &lt;text&gt;\n</pre>" in out
    assert "before" in out
    assert "after" in out


def test_title_words_defaults_when_empty():
    assert title_words(None) == "(SEM TÍTULO)"
    assert title_words("  ") == "(SEM TÍTULO)"


def test_session_block_includes_header_and_body():
    block = session_block("Pronto.", "abc12345", "hello world session", body="oi")
    assert "Pronto." in block
    assert "[ABC]" in block
    assert "HELLO WORLD SESSION" in block
    assert "oi" in block
