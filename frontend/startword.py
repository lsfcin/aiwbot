# startword.py — does a message open with the "bot" session-start word, and what follows it.
from __future__ import annotations

# STT hears "bote" for "bot" often enough that the session-start intent silently never fired
# (INBOX 2026-07-24). Normalizing the misheard form beats picking a new start word: "bot" is
# already muscle memory, and any replacement would collect mishearings of its own. "bote "
# cannot collide with "bot " — the character after "bot" there is `e`, not a separator.
_WORDS = ("bot", "bote")
_SEPS = (" ", ",")


def _marker(lowered: str) -> str | None:
    """The `bot `/`bote,`-style opener this text begins with, if any."""
    found = None
    for word in _WORDS:
        for sep in _SEPS:
            candidate = word + sep
            if lowered.startswith(candidate):
                found = candidate
                break
        if found:
            break
    return found


def strip_prefix(text: str) -> str | None:
    """The prompt after the start word, or None when the text does not open with one."""
    lowered = text.lower()
    marker = _marker(lowered)
    prompt = None
    if marker:
        rest = text[len(marker):]
        prompt = rest.strip()
    return prompt
