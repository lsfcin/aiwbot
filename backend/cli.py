# cli.py — CliBackend: the single subprocess-driven send() loop; subclasses supply build_args + parse.
from __future__ import annotations
from typing import AsyncIterator
from .base import AgentEvent, TurnOptions
from .caps import Capabilities
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

    def session_detail(self, session_id: str, cwd: str) -> dict:
        """Default: the list already carried everything. Backends whose store needs a
        per-session query put the expensive fields here instead, so the picker pays for
        the page it renders rather than for every session it lists."""
        return {}

    def occupancy(self, session_id: str, cwd: str) -> int | None:
        """Context-window occupancy after the turn, read from the provider's own store.
        Default: unknown. Backends that record per-message token usage override this."""
        return None

    def env(self) -> dict | None:
        """Extra environment for the subprocess. Default: none — backends override."""
        return None

    def capabilities(self) -> Capabilities:
        """Default: nothing selectable, so the panel simply shows no rows for this backend."""
        return Capabilities()

    def efforts(self, model: str | None = None) -> list[str]:
        """Default: no effort knob. Backends whose CLI has one override this."""
        return []

    async def send(self, prompt: str, *, session_id: str | None, cwd: str,
                   options: TurnOptions = TurnOptions()) -> AsyncIterator[AgentEvent]:
        args = self.build_args(prompt, session_id, options)
        extra_env = self.env()
        out, err, code = await run_capture(args, cwd, extra_env)
        events = events_from_run(out, err, code, self.parse)
        self._attach_occupancy(events, cwd)
        for event in events:
            yield event

    def _attach_occupancy(self, events: list[AgentEvent], cwd: str) -> None:
        """Occupancy is a property of the turn's LAST request, never of its total spend — a
        turn that used tools made several requests and each re-read the whole context, so any
        sum over them measures money, not how full the window is (b3). Every CLI's own store
        records the per-message breakdown, so it is read from there rather than from whatever
        the run's summary object happened to aggregate."""
        for event in events:
            if event.kind == "result" and event.session_id:
                measured = self.occupancy(event.session_id, cwd)
                if measured is not None:
                    event.context_used = measured
