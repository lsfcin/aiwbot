# __init__.py — facade: seam types + backend registry. Import backends only through here.
from .base import AgentEvent, AgentBackend, EventKind
from .claude import ClaudeBackend
from .opencode import OpencodeBackend

_BACKENDS = {"claude": ClaudeBackend, "opencode": OpencodeBackend}


def get_backend(name: str) -> AgentBackend:
    factory = _BACKENDS.get(name)
    if factory is None:
        raise ValueError(f"unknown backend: {name}")
    instance = factory()
    return instance


__all__ = ["AgentEvent", "AgentBackend", "EventKind", "get_backend"]
