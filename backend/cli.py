# cli.py — CliBackend: the single subprocess-driven send() loop; subclasses supply build_args + parse.
from __future__ import annotations
from typing import AsyncIterator
from .base import AgentEvent
from .proc import run_capture, events_from_run


class CliBackend:
    name: str = "cli"

    def build_args(self, prompt: str, session_id: str | None) -> list[str]:
        raise NotImplementedError

    def parse(self, stdout: str) -> list[AgentEvent]:
        raise NotImplementedError

    async def send(self, prompt: str, *, session_id: str | None, cwd: str) -> AsyncIterator[AgentEvent]:
        args = self.build_args(prompt, session_id)
        out, err, code = await run_capture(args, cwd)
        events = events_from_run(out, err, code, self.parse)
        for event in events:
            yield event
