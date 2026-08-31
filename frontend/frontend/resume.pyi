from . import config as config, format as format, msgmap as msgmap, panelmenu as panelmenu, phrases as phrases, registry as registry, reply as reply, sessions as sessions

RESUME_COUNT: int
TITLE_WORDS: int
QUERY_MAX: int
RULER_WIDTH: int

async def cmd_resume(msg, arg: str, cwd: str) -> None: ...
async def handle_callback(update, context) -> None: ...
