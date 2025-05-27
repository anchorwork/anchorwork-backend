from fastapi import APIRouter, Query
from typing import Optional

from crew.brainstorm_orchestrator import run_crew_brainstorm, format_crew_brainstorm_output
from crew.ritual_synthesis import synthesize_ritual
from crew.crew_history import load_crew_history, format_crew_history_entry, search_crew_history

router = APIRouter(prefix="/crew", tags=["crew"])

@router.post("/brainstorm")
async def crew_brainstorm():
    responses, formatted_output = run_crew_brainstorm()
    return {"responses": responses, "formatted_output": formatted_output}

@router.post("/ritual_synthesis")
async def crew_ritual_synthesis():
    ritual = synthesize_ritual()
    return {"ritual": ritual}

@router.get("/history")
async def crew_history(n: Optional[int] = Query(10, description="Number of history entries to retrieve")):
    history = load_crew_history(n)
    history_entries = [format_crew_history_entry(entry) for entry in history]
    return {"history": history_entries}

@router.get("/history/search")
async def crew_history_search(keyword: str = Query(..., description="Keyword to search in history entries")):
    matched = search_crew_history(keyword)
    matched_entries = [format_crew_history_entry(entry) for entry in matched]
    return {"matched_entries": matched_entries}
