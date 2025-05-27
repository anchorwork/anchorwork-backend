"""
Anchorwork Crew History & Logbook
---------------------------------
Records, retrieves, and searches major crew council sessions, rituals, and events.
This becomes the “collective memory” of the Anchorwork crew.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

LOG_DIR = Path("memory")
LOG_FILE = LOG_DIR / "crew_history.jsonl"
LOG_DIR.mkdir(exist_ok=True)

def log_crew_event(event_type: str, prompt: str, council_responses: Dict[str, str], summary: Optional[str] = None, tags: Optional[List[str]] = None) -> None:
    """
    Records a council session or event to the log.
    """
    entry = {
        "timestamp": str(datetime.utcnow()),
        "event_type": event_type,
        "prompt": prompt,
        "council_responses": council_responses,
        "summary": summary or "",
        "tags": tags or []
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def load_crew_history(n: int = 50) -> List[Dict[str, Any]]:
    """
    Loads the most recent n events from crew history.
    """
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()[-n:]
    return [json.loads(line) for line in lines]

def search_crew_history(keyword: str, n: int = 100) -> List[Dict[str, Any]]:
    """
    Searches the crew history log for entries matching the keyword in prompt, summary, or any response.
    """
    results = []
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            haystack = (entry["prompt"] + " " + entry["summary"] + " " + " ".join(entry["council_responses"].values())).lower()
            if keyword.lower() in haystack:
                results.append(entry)
                if len(results) >= n:
                    break
    return results

def format_crew_history_entry(entry: Dict[str, Any]) -> str:
    """
    Nicely formats a crew history entry for display.
    """
    lines = [f"\n[Log Timestamp: {entry['timestamp']} | Event: {entry['event_type']}]"]
    lines.append(f"Prompt: {entry['prompt']}")
    if entry["summary"]:
        lines.append(f"Summary: {entry['summary']}")
    lines.append("Crew Responses:")
    for name, response in entry["council_responses"].items():
        lines.append(f"  - {name}: {response[:120]}...")
    if entry["tags"]:
        lines.append(f"Tags: {', '.join(entry['tags'])}")
    return "\n".join(lines)

# Example usage:
if __name__ == "__main__":
    # Demo: log and display a crew council event
    test_prompt = "What’s our best ritual for navigating uncertainty?"
    mock_responses = {
        "First Matey": "Let’s craft a hope anchor and cast it into the unknown.",
        "Cartographer": "Draw a star map for your next month.",
        "Compass": "Focus on your true north—your deepest values.",
        "Watcher": "Remember: calm often follows the greatest storms.",
        "Alchemist": "Mix a tea of surprise—sip, savor, let go.",
        "Coder": "Build a daily 'uncertainty tracker' in your journal."
    }
    log_crew_event("council_brainstorm", test_prompt, mock_responses, summary="Crew shared rituals for uncertainty.", tags=["ritual", "uncertainty"])
    history = load_crew_history(3)
    for entry in history:
        print(format_crew_history_entry(entry))