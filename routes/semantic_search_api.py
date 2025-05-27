"""
Semantic Search API

This API provides an endpoint to perform semantic search queries.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Any, Dict
from utils.semantic_search import semantic_search

router = APIRouter()

class SemanticSearchRequest(BaseModel):
    query: str

@router.post("/semantic_search")
async def run_semantic_search(request: SemanticSearchRequest) -> Dict[str, Any]:
    """
    Perform a semantic search based on the provided query.

    Args:
        request (SemanticSearchRequest): The request body containing the search query.

    Returns:
        Dict[str, Any]: A dictionary containing the search matches or an error message.
    """
    try:
        results = semantic_search(request.query)
        return {"matches": results}
    except Exception as e:
        return {"error": str(e)}
