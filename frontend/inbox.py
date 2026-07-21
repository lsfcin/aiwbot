# inbox.py — capture plain text/media into brain/INBOX.md ($0, no backend call).
from __future__ import annotations
import pathlib
import sys
from datetime import datetime
from telegram.ext import ContextTypes

sys.path.insert(0, str(pathlib.Path("/mnt/workspace/core/tools")))
import attachments_util  # noqa: E402

BRAIN_ATTACHMENTS = pathlib.Path("/mnt/workspace/brain/attachments")
INBOX_FILE = pathlib.Path("/mnt/workspace/brain/INBOX.md")
INBOX_MARKER = "<!-- add entries below, newest first -->"


def append_entry(entry: str) -> None:
    text = INBOX_FILE.read_text()
    marker_pos = text.index(INBOX_MARKER) + len(INBOX_MARKER)
    updated = text[:marker_pos] + f"\n\n{entry}" + text[marker_pos:]
    INBOX_FILE.write_text(updated)


def build_entry(body: str, attachment_path: pathlib.Path | None) -> str:
    date = datetime.now().strftime("%Y-%m-%d")
    lines = [body]
    if attachment_path is not None:
        lines.append(f"[attachment: {attachment_path.relative_to('/mnt/workspace')}]")
    lines.append(f"— via aiwbot · {date}")
    return "\n".join(lines)


async def save_media(file_id: str, context: ContextTypes.DEFAULT_TYPE, suffix: str) -> pathlib.Path:
    tg_file = await context.bot.get_file(file_id)
    month_dir = attachments_util.month_dir(BRAIN_ATTACHMENTS)
    filename = attachments_util.safe_name(f"aiwbot-{file_id}{suffix}")
    filepath = attachments_util.unique_path(month_dir / filename)
    await tg_file.download_to_drive(str(filepath))
    return filepath
