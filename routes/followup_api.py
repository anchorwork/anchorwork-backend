"""Follow-up generator API — provides an endpoint to append short messages to a log file."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

LOG_PATH = Path("data/followup_log.txt")
router = APIRouter(prefix="/followup", tags=["follow-up"])


class FollowupNote(BaseModel):
    """Request model for a follow-up note."""
    note: str


def _write_line(text: str) -> None:
    """Append *text* to the follow-up log using UTF-8 encoding.

    Raises:
        IOError: If writing to the log file fails.
    """
    LOG_PATH.parent.mkdir(exist_ok=True)
    try:
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")
    except IOError as e:
        raise IOError(f"Failed to write to log file: {e}")


@router.post("/", summary="Add a follow-up note")
async def add_followup(followup: FollowupNote) -> dict:
    """Add a follow-up note to the log and return the new total line count.

    Args:
        followup (FollowupNote): The follow-up note to add.

    Returns:
        dict: Contains the saved note and the total number of lines in the log.

    Raises:
        HTTPException: If the note is blank or writing to the log fails.
    """
    note = followup.note.strip()
    if not note:
        raise HTTPException(status_code=400, detail="Note cannot be blank")

    try:
        _write_line(note)
    except IOError as e:
        raise HTTPException(status_code=500, detail=str(e))

    line_count = sum(1 for _ in LOG_PATH.open("r", encoding="utf-8"))
    return {"saved": note, "total_lines": line_count}
