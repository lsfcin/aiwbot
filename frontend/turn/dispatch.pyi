from dataclasses import dataclass

@dataclass
class TurnResult:
    text: str
    session_id: str
    cost_usd: float | None

class DispatchError(Exception): ...

async def turn(prompt: str, *, session_id: str | None, backend_name: str, cwd: str) -> TurnResult: ...
