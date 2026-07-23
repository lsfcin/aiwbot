# cli.py — CliBackend: the single subprocess-driven send() loop; subclasses supply build_args + parse.
from __future__ import annotations
from typing import AsyncIterator
from .base import AgentEvent, TurnOptions
from .proc import run_capture, events_from_run


class CliBackend:
    name: str = "cli"

    def build_args(self, prompt: str, session_id: str | None, options: TurnOptions) -> list[str]:
        raise NotImplementedError

    def parse(self, stdout: str) -> list[AgentEvent]:
        raise NotImplementedError

    def list_sessions(self, cwd: str) -> list[dict]:
        """Default: provider exposes no session store. Backends with one override this."""
        return []

    def last_response(self, session_id: str, cwd: str) -> str:
        """Default: provider exposes no transcript. Backends with one override this."""
        return ""

    def env(self) -> dict | None:
        """Extra environment for the subprocess. Default: none — backends override."""
        return None

    async def send(self, prompt: str, *, session_id: str | None, cwd: str,
                   options: TurnOptions = TurnOptions()) -> AsyncIterator[AgentEvent]:
        args = self.build_args(prompt, session_id, options)
        extra_env = self.env()
        out, err, code = await run_capture(args, cwd, extra_env)
        events = events_from_run(out, err, code, self.parse)
        for event in events:
            yield event
