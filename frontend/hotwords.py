# hotwords.py — explicit editable data (C4): faster-whisper's `hotwords=` prompt seed.
# Kept as data, not inline in stt.py, so the list can be tuned without touching wrapper logic.
from __future__ import annotations

HOTWORDS = [
    # workspace jargon
    "aiwbot", "isoroll", "spacemantics", "dobra", "cria", "instituto", "casinhas",
    "roadmap", "INBOX", "backend", "opencode", "commit", "deploy", "prompt",
    "dispatch", "harness",
    # English loanwords Portuguese speech commonly borrows verbatim
    "workspace", "feature", "branch", "merge", "pull request", "token",
    "prompt engineering", "framework", "pipeline", "webhook",
]


def as_prompt() -> str:
    return " ".join(HOTWORDS)
