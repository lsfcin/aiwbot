# hotwords.py — explicit editable data (C4): what the STT is primed with before it listens.
# Kept as data, not inline in stt.py, so it can be tuned without touching wrapper logic.
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

# Whisper imitates the *style* of what it is primed with, so a carrier written in Lucas's own
# register, correctly punctuated, is what buys punctuation back — measured on his own 15 voice
# notes, this moved "bote me diz o que é que tem de e-mail gente" (zero punctuation) to
# "Bot, me diz o que que tem de e-mail, gente."
#
# The jargon rides INSIDE the carrier rather than in faster-whisper's separate `hotwords=` arg,
# because the two compete for the same conditioning slot: priming for punctuation alone cost the
# vocabulary ("bote" came back as "Pode", losing the session-start word entirely). One prompt
# carrying both is what serves both. The carrier opens with "Bot," for exactly that reason.
CARRIER = [
    "Bot, roda os testes do aiwbot e me diz o que quebrou.",
    "Bot, abre o roadmap do isoroll e do spacemantics.",
    "Beleza, então é o seguinte: se der erro no opencode ou no claude, manda o log.",
    "Tudo bem? Ah, e não esquece do commit.",
]


def as_prompt() -> str:
    """The full conditioning prompt: punctuated carrier sentences, then the jargon list."""
    carrier = " ".join(CARRIER)
    words = " ".join(HOTWORDS)
    return f"{carrier} {words}"
