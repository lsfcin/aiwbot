# tests
> Free unit tests — pure-logic fixtures/parsers/formatting, no network or cost.
> spec: none

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | — | — | **facade** — __init__.py — marks tests as a package. |
| [`test_bot.py`](test_bot.py) | — | `test_strip_bot_prefix_space`, `test_strip_bot_prefix_comma`, `test_strip_bot_prefix_case_insensitive`, `test_strip_bot_prefix_no_match` | test_bot.py — free unit test: "bot"-prefix trigger routing logic. |
| [`test_dispatch.py`](test_dispatch.py) | — | `test_claude_fixture_consolidates_to_result`, `test_opencode_fixture_consolidates_to_result`, `test_error_event_raises_dispatch_error`, `test_missing_result_event_raises_dispatch_error`, `test_model_flows_from_result_event` | test_dispatch.py — free unit test: AgentEvent list -> TurnResult, using Phase A fixtures. |
| [`test_format.py`](test_format.py) | — | `test_plain_markdown_to_html`, `test_pipe_table_boxed_as_pre`, `test_fenced_code_block_boxed_as_pre`, `test_title_words_defaults_when_empty`, `test_session_block_includes_header_and_body` | test_format.py — free unit test: markdown/table -> Telegram HTML conversion. |
| [`test_parse_claude.py`](test_parse_claude.py) | — | `test_claude_has_text_and_result`, `test_claude_text_and_session`, `test_claude_contract`, `test_resume_is_single_lineage_no_fork` | test_parse_claude.py — free unit test: claude fixture -> normalized AgentEvents satisfy the contract. |
| [`test_parse_opencode.py`](test_parse_opencode.py) | — | `test_opencode_has_text_and_result`, `test_opencode_text_and_session`, `test_opencode_contract` | test_parse_opencode.py — free unit test: opencode JSONL fixture -> AgentEvents satisfy the contract. |
| [`test_resume.py`](test_resume.py) | — | `test_label_three_lines_with_preview`, `test_label_omits_preview_line_when_absent`, `test_truncate_adds_ellipsis_over_limit`, `test_truncate_leaves_short_text_untouched` | test_resume.py — free unit test: /resume picker button label assembly. |
<!-- routing:end -->
