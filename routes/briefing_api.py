"""Briefing API — save concise topic briefings as Markdown files.

This API provides an endpoint to create briefings on given topics.
Each briefing is saved as a Markdown file with a timestamped filename.
"""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/briefing", tags=["briefing"])

BRIEF_DIR = Path("briefings")
BRIEF_DIR.mkdir(exist_ok=True)


def _timestamp() -> str:
    """Return a UTC timestamp suitable for filenames."""
    return datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")


class BriefingRequest(BaseModel):
    topic: str
    body: str


@router.post("/", summary="Create a briefing for a topic")
async def create_briefing(request: BriefingRequest) -> dict:
    """
    Save *body* to a new Markdown file under ``briefings/`` named
    ``<timestamp>_<topic>.md`` and return the filename.

    Parameters
    ----------
    request : BriefingRequest
        Request model containing the briefing topic and markdown content.

    Returns
    -------
    dict
        ``{"saved": "<relative path>"}``
    """
    topic_clean = request.topic.strip()
    body_clean = request.body.strip()

    if not topic_clean or not body_clean:
        raise HTTPException(
            status_code=400,
            detail="Both 'topic' and 'body' must be non-empty strings.",
        )

    fname = f"{_timestamp()}_{topic_clean.replace(' ', '_')}.md"
    path = BRIEF_DIR / fname

    # Always write UTF-8 to avoid encoding warnings (bandit/pylint W1514).
    try:
        with path.open("w", encoding="utf-8") as md_file:
            md_file.write(f"# {topic_clean}\n\n")
            md_file.write(body_clean + "\n")
    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save briefing file: {e}",
        )

    return {"saved": str(path)}
