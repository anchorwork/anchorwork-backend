"""Minimal web-search endpoint.

Uses the shared utils.web_search.web_search helper and returns the raw hits.

This module provides a FastAPI endpoint to perform web searches using a structured request model.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from utils.web_search import web_search

router = APIRouter(prefix="/web-search", tags=["search"])


class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 5


@router.post("/", summary="Run a quick web search")
async def web_search_endpoint(request: WebSearchRequest) -> dict:
    """Search the web for *query* and return the top *max_results* links."""
    try:
        hits = web_search(request.query, num_results=request.max_results)
        return {"query": request.query, "results": hits}
    except Exception as e:
        return {"error": "Failed to perform web search", "details": str(e)}
