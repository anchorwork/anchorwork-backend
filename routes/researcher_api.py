"""Research helper — runs a web search and saves a local Markdown brief.

This module provides a POST endpoint to generate a research brief for a given topic.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
from utils.web_search import web_search

router = APIRouter(prefix="/research", tags=["research"])
BRIEF_DIR = Path("research_briefs")
BRIEF_DIR.mkdir(exist_ok=True)


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")


class ResearchRequest(BaseModel):
    topic: str
    top_k: int = 5


@router.post("/", summary="Generate a brief for the given topic")
async def create_brief(request: ResearchRequest) -> dict:
    """Search `request.topic`, save a brief, and return its filename and hits.

    Args:
        request (ResearchRequest): The research request containing topic and top_k.

    Returns:
        dict: Contains the file path and the hits string.
    """
    try:
        hits = web_search(request.topic, num_results=request.top_k)
        filename = BRIEF_DIR / f"{_timestamp()}_{request.topic.replace(' ', '_')}.md"

        with filename.open("w", encoding="utf-8") as md:
            md.write(f"# Research brief — **{request.topic}**\n\n")
            md.write(hits)

        return {"file": str(filename), "hits": hits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create brief: {e}")
