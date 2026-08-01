# seam
> The AgentBackend seam: a CLI's output becomes AgentEvents, and a turn's options reach its argv.
> spec: none

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — marks tests/seam as a package. |
| [`test_b2_opencode_error.py`](test_b2_opencode_error.py) | — | test_b2_opencode_error.py — regression spec for [b2]: opencode failures collapsing to the |
| [`test_b4_opencode_cwd.py`](test_b4_opencode_cwd.py) | `communicate`, `fake_exec`, `drain` | test_b4_opencode_cwd.py — regression spec for [b4]: turns ran in the daemon's launch directory. |
| [`test_dispatch.py`](test_dispatch.py) | — | test_dispatch.py — free unit test: AgentEvent list -> TurnResult, using Phase A fixtures. |
| [`test_parse_claude.py`](test_parse_claude.py) | — | test_parse_claude.py — free unit test: claude fixture -> normalized AgentEvents satisfy the contract. |
| [`test_parse_opencode.py`](test_parse_opencode.py) | — | test_parse_opencode.py — free unit test: opencode JSONL fixture -> AgentEvents satisfy the contract. |
| [`test_target.py`](test_target.py) | — | test_target.py — free unit test: model/effort reach the argv, and each backend's declaration. |
<!-- routing:end -->
