"""API route to save log entries to a JSON file."""

from fastapi import APIRouter, Request
from datetime import datetime
import os
import json

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CODEX_PATH = os.path.join(BASE_DIR, "codex.json")


@router.post("/save_log")
async def save_log(request: Request) -> dict:
    """
    Save a log entry received in the request body to the codex.json file.

    Args:
        request (Request): The incoming request containing log data.

    Returns:
        dict: A dictionary containing the status and the saved log entry or an error message.
    """
    try:
        body = await request.json()
        log_entry = {
            "author": body.get("author", "unknown"),
            "action": body.get("action", "unspecified"),
            "target": body.get("target", "manual"),
            "content": body.get("content", ""),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if not os.path.exists(CODEX_PATH):
            with open(CODEX_PATH, "w") as f:
                json.dump([], f)

        with open(CODEX_PATH, "r+") as f:
            logs = json.load(f)
            logs.append(log_entry)
            f.seek(0)
            # Consider using atomic write operations here for robustness in future
            json.dump(logs, f, indent=2)

        return {"status": "success", "log": log_entry}

    except Exception as e:
        return {"status": "error", "message": str(e)}
