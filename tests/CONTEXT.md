# tests
> Free unit tests — pure-logic fixtures/parsers/formatting, no network or cost.
> spec: none

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — marks tests as a package. |
| [`chatkit.py`](chatkit.py) | `Bubble`, `Chat`, `Origin`, `edit_text`, `delete` | chatkit.py — shared Telegram fakes: a chat that records every write, its bubbles, and the |
| [`conftest.py`](conftest.py) | `store` | conftest.py — fixtures shared by the panel tests: an in-memory config and a fake backend. |
| [`panelkit.py`](panelkit.py) | `Fake`, `labels`, `texts`, `data`, `capabilities` | panelkit.py — shared panel-test scaffolding: a fake backend plus keyboard readers. |
| [`streamkit.py`](streamkit.py) | `deltas`, `result`, `FakeStream`, `Clock`, `send` | streamkit.py — shared streaming-test scaffolding: an async-generator fake backend and a clock. |
| [`test_b1_table_bold.py`](test_b1_table_bold.py) | — | test_b1_table_bold.py — regression spec for [b1]: tables and bold not rendering in Telegram. |
| [`test_b2_opencode_error.py`](test_b2_opencode_error.py) | — | test_b2_opencode_error.py — regression spec for [b2]: opencode failures collapsing to the |
| [`test_b3_context_pct.py`](test_b3_context_pct.py) | `occupancy`, `occupancy` | test_b3_context_pct.py — regression spec for [b3]: context occupancy over 100% (even 200%). |
| [`test_b4_opencode_cwd.py`](test_b4_opencode_cwd.py) | `communicate`, `fake_exec`, `drain` | test_b4_opencode_cwd.py — regression spec for [b4]: turns ran in the daemon's launch directory. |
| [`test_bot.py`](test_bot.py) | — | test_bot.py — free unit test: "bot"-prefix trigger routing logic. |
| [`test_catalog.py`](test_catalog.py) | — | test_catalog.py — free unit test: opencode catalogue — effort vocabularies, groups, favourites. |
| [`test_directives.py`](test_directives.py) | — | test_directives.py — F3a: read leading harness/model words off a bot-prefixed message, $0. |
| [`test_dispatch.py`](test_dispatch.py) | — | test_dispatch.py — free unit test: AgentEvent list -> TurnResult, using Phase A fixtures. |
| [`test_f2_papercuts.py`](test_f2_papercuts.py) | — | test_f2_papercuts.py — the F2 batch: phrase tone, flat glyphs, the reply anchor, and the |
| [`test_f3c_tap_latency.py`](test_f3c_tap_latency.py) | `answer`, `edit_message_reply_markup`, `capabilities`, `efforts` | test_f3c_tap_latency.py — F3c: a panel tap costs ONE Telegram round trip, not two or three. |
| [`test_f4_ask.py`](test_f4_ask.py) | `go`, `go`, `go`, `go`, `go` | test_f4_ask.py — F4 Stage 4: the broker. One asyncio.Future per question, the chat UX that |
| [`test_f4_ask_wiring.py`](test_f4_ask_wiring.py) | — | test_f4_ask_wiring.py — F4 Stage 4: the transport and the CLI wiring around the broker. |
| [`test_f4_frames.py`](test_f4_frames.py) | — | test_f4_frames.py — F4 Stage 2: what may be RENDERED mid-stream, and the guarantee that a |
| [`test_f4_sealing.py`](test_f4_sealing.py) | `go`, `go` | test_f4_sealing.py — F4 Stage 3: bubbles sealed as they are born, and the property that makes |
| [`test_f4_streaming.py`](test_f4_streaming.py) | `send_action`, `edit_text`, `run`, `run`, `timed` | test_f4_streaming.py — F4 Stage 2: the live bubble. Throttle mechanics, the pin, and the |
| [`test_f5_answer_shape.py`](test_f5_answer_shape.py) | `reply_text` | test_f5_answer_shape.py — F5: a long answer arrives as several repliable bubbles. |
| [`test_f6_bubble_shape.py`](test_f6_bubble_shape.py) | `go`, `go`, `go` | test_f6_bubble_shape.py — the furniture on a bubble, decided by Lucas on 2026-07-28: the voice |
| [`test_f6_interview_shape.py`](test_f6_interview_shape.py) | `go` | test_f6_interview_shape.py — what the chat looks like when the agent interviews Lucas mid-turn |
| [`test_f6_pacing.py`](test_f6_pacing.py) | `timed`, `run` | test_f6_pacing.py — the pause BETWEEN bubbles (Lucas, 2026-07-28). Distinct from the repaint |
| [`test_f6_voice_feedback.py`](test_f6_voice_feedback.py) | `fake_save`, `fake_route`, `fake_edit`, `fake_safe_reply`, `fake_turn` | test_f6_voice_feedback.py — a voice note says something back before it has been transcribed |
| [`test_f7_opencode_ask.py`](test_f7_opencode_ask.py) | — | test_f7_opencode_ask.py — opencode parity: the ask transport and the retry vocabulary. |
| [`test_f8_ask_answer_shape.py`](test_f8_ask_answer_shape.py) | `go`, `answer_now`, `answer_now`, `tap_second`, `answer_now` | test_f8_ask_answer_shape.py — what an interview looks like in the chat, from Lucas reading a real |
| [`test_f8_footer_model.py`](test_f8_footer_model.py) | — | test_f8_footer_model.py — Lucas, live 2026-07-29: an opencode answer's footer named no model. |
| [`test_format.py`](test_format.py) | — | test_format.py — free unit test: markdown/table -> Telegram HTML conversion. |
| [`test_hotwords.py`](test_hotwords.py) | — | test_hotwords.py — free unit test: hotwords is explicit editable data (C4), not inline in stt.py. |
| [`test_htmlsplit.py`](test_htmlsplit.py) | — | test_htmlsplit.py — free unit test: chunking formatted HTML without breaking a tag. |
| [`test_inbox.py`](test_inbox.py) | — | test_inbox.py — free unit test: build_entry tags forwarded (non-Lucas) captures. |
| [`test_labels.py`](test_labels.py) | — | test_labels.py — free unit test: fitting a model id into a button label. |
| [`test_markdown.py`](test_markdown.py) | — | test_markdown.py — free unit test: block + inline markdown -> Telegram HTML. |
| [`test_ocstore.py`](test_ocstore.py) | — | test_ocstore.py — free unit test: opencode sqlite reads — last assistant turn + occupancy. |
| [`test_panel.py`](test_panel.py) | `answer`, `edit_message_reply_markup` | test_panel.py — free unit test: panel effects — scopes, applying a choice, hidden dims. |
| [`test_panelmenu.py`](test_panelmenu.py) | — | test_panelmenu.py — free unit test: panel layout — rows, controls, ordering, paging. |
| [`test_parse_claude.py`](test_parse_claude.py) | — | test_parse_claude.py — free unit test: claude fixture -> normalized AgentEvents satisfy the contract. |
| [`test_parse_opencode.py`](test_parse_opencode.py) | — | test_parse_opencode.py — free unit test: opencode JSONL fixture -> AgentEvents satisfy the contract. |
| [`test_registry.py`](test_registry.py) | `store` | test_registry.py — free unit test: scopes (session vs NEW), last-used defaults, message maps. |
| [`test_reply_voice.py`](test_reply_voice.py) | `FakeMsg`, `FailingMsg`, `reply_voice`, `reply_voice` | test_reply_voice.py — free unit test: reply.send_voice (C5), mirrors safe_reply's Telegram-error |
| [`test_resume.py`](test_resume.py) | — | test_resume.py — free unit test: /resume picker list/label/pagination assembly. |
| [`test_route_text.py`](test_route_text.py) | `FakeReplyAnchor`, `FakeMsg`, `testrun_and_deliver_spoken_sends_voice_in_addition_to_text`, `testrun_and_deliver_not_spoken_never_sends_voice`, `fake_start_new` | test_route_text.py — free unit test: shared text/voice routing (_route_text), the C3 |
| [`test_sessions.py`](test_sessions.py) | `two_backends`, `list_sessions`, `session_detail` | test_sessions.py — free unit test: cross-backend /resume aggregation + registry adopt/mode. |
| [`test_speech.py`](test_speech.py) | — | test_speech.py — free unit test: markdown answer -> prose a TTS voice can read (F3b). |
| [`test_stream_parse.py`](test_stream_parse.py) | `consume` | test_stream_parse.py — F4 Stage 1: claude's stream-json becomes deltas, and the turn still |
| [`test_stt.py`](test_stt.py) | `FakeSegment`, `FakeModel`, `transcribe`, `BoomModel`, `transcribe` | test_stt.py — free unit test: STT wrapper (C1 transcription, C3 fail-safe, C6 no live calls). |
| [`test_target.py`](test_target.py) | — | test_target.py — free unit test: model/effort reach the argv, and each backend's declaration. |
| [`test_transcript.py`](test_transcript.py) | — | test_transcript.py — free unit test: tail-scan a claude .jsonl for title/preview/model. |
| [`test_tts.py`](test_tts.py) | `FakePipeline` | test_tts.py — free unit test: TTS wrapper (C5 voice reply) + local OGG/Opus encode (C6, no live calls). |
| [`test_voice_echo_and_picker.py`](test_voice_echo_and_picker.py) | — | test_voice_echo_and_picker.py — Lucas's 2026-07-27 live test: STT conditioning prompt shape, |
<!-- routing:end -->
