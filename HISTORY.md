# aiwbot — History
> Archive of completed work. Open work lives in [ROADMAP.md](ROADMAP.md).

## Completed — 2026-07-21

### Phase A — prove the provider-agnostic seam
- `AgentBackend`/`AgentEvent` seam + `CliBackend` driver + `check_contract` (backend/base.py, cli.py).
- `claude` + `opencode` backends: `build_args` + pure `parse_events` (backend/claude.py, opencode.py).
- Free fixture unit tests — 6 green (`make test`, tests/).
- Live smoke (`make smoke`): both backends pass end-to-end + single-lineage resume. **Risk retired** —
  the one interface holds across a forking backend (claude, `--fork-session`, new id/turn) and a
  same-lineage backend (opencode, `-s`, same id). Frontend chases `result.session_id` (AD-3, SPECS.md).
- Gitflow: scaffold on `main` → Phase A on `feature/agent-backend-seam` → merged to `develop`.
