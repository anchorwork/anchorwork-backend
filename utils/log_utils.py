import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

LOG_STORE_PATH = Path("logs/log_store.json")
CODEX_PATH = Path("logs/codex.json")

def ensure_log_store() -> None:
    """
    Ensure that the log store file exists. If not, create an empty log store.
    """
    if not LOG_STORE_PATH.exists():
        LOG_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_STORE_PATH, 'w') as f:
            json.dump([], f)

def load_log_store() -> List[Dict[str, Any]]:
    """
    Load the log store from the JSON file.

    Returns:
        List of log entries.
    """
    ensure_log_store()
    with open(LOG_STORE_PATH, 'r') as f:
        return json.load(f)

def save_to_log_store(logs: List[Dict[str, Any]]) -> None:
    """
    Save the list of log entries to the log store JSON file.

    Args:
        logs: List of log entries to save.
    """
    with open(LOG_STORE_PATH, 'w') as f:
        json.dump(logs, f, indent=2)

def log_interaction(prompt: str, response: str, agent: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Log an interaction with prompt, response, agent, and optional tags.

    Args:
        prompt: The prompt string.
        response: The response string.
        agent: The agent name.
        tags: Optional list of tags.

    Returns:
        The log entry dictionary that was added.
    """
    if tags is None:
        tags = []
    logs = load_log_store()
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": agent,
        "prompt": prompt,
        "response": response,
        "tags": tags
    }
    logs.append(log_entry)
    save_to_log_store(logs)
    return log_entry

def update_log_entry(log_id: str, updated_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a log entry in the log store by its ID.

    Args:
        log_id: The ID of the log entry to update.
        updated_fields: A dictionary of fields to update.

    Returns:
        The updated log entry.

    Raises:
        ValueError: If the log entry with the given ID is not found.
    """
    logs = load_log_store()
    for log in logs:
        if log.get("id") == log_id:
            log.update(updated_fields)
            save_to_log_store(logs)
            return log
    raise ValueError("Log entry not found.")

def log_to_codex(agent: str, prompt: str, response: str, tags: Optional[List[str]] = None) -> None:
    """
    Log an interaction to the codex log file.

    Args:
        agent: The agent name.
        prompt: The prompt string.
        response: The response string.
        tags: Optional list of tags.
    """
    if tags is None:
        tags = []
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": agent,
        "prompt": prompt,
        "response": response,
        "tags": tags
    }
    if not CODEX_PATH.exists():
        with open(CODEX_PATH, "w") as f:
            json.dump({"log": []}, f, indent=2)
    with open(CODEX_PATH, "r") as f:
        codex = json.load(f)
    codex["log"].append(log_entry)
    with open(CODEX_PATH, "w") as f:
        json.dump(codex, f, indent=2)

def search_codex(keyword: str) -> List[Dict[str, Any]]:
    """
    Search the codex log entries for the given keyword in prompt, response, agent, or tags.

    Args:
        keyword: The keyword to search for.

    Returns:
        A list of matching log entries.
    """
    if not CODEX_PATH.exists():
        return []
    with open(CODEX_PATH, "r") as f:
        codex = json.load(f)
    keyword_lower = keyword.lower()
    results = []
    for entry in codex.get("log", []):
        if (keyword_lower in entry.get("prompt", "").lower() or
            keyword_lower in entry.get("response", "").lower() or
            keyword_lower in entry.get("agent", "").lower() or
            any(keyword_lower in tag.lower() for tag in entry.get("tags", []))):
            results.append(entry)
    return results
