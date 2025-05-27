"""
This module defines the '/codex/search' route, which allows clients to search the codex using a provided keyword.
The endpoint expects a POST request with a JSON body containing the search keyword, and returns the matching results.
"""

from fastapi import APIRouter, Request
from fastapi import HTTPException
from pydantic import BaseModel
from utils.log_utils import search_codex

router = APIRouter()


class CodexSearchRequest(BaseModel):
    keyword: str


@router.post("/codex/search")
async def codex_search(
    req: CodexSearchRequest,
) -> dict:
    """
    Search the codex for entries matching the given keyword.
    
    Args:
        req (CodexSearchRequest): The search request containing the keyword.
    Returns:
        dict: A dictionary with the search matches or an error message.
    """
    try:
        results = search_codex(req.keyword)
        return {"matches": results}
    except Exception as e:
        # Optionally log the error here
        return {"error": "An unexpected error occurred.", "detail": str(e)}
