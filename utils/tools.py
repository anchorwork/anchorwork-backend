# utils/tools.py
"""
Utility helpers that multiple modules import.

• web_search          – stub (drop real impl later)
• semantic_search     – stub
• load_agent_profile  – required by agents
"""

from pathlib import Path
import json, random
from utils.semantic_search import semantic_search
from utils.web_search import web_search

# ── fun helpers (optional) ──────────────────────────────────────────
PEP_TALKS = [
    "Calm seas never made a skilled sailor.",
    "Anchor deep and steer true!",
]
def get_pep_talk() -> str:
    """
    Return a random motivational phrase from the PEP_TALKS list.
    """
    return random.choice(PEP_TALKS)

SHANTIES = [
    "🎶 Oh the anchor drops, the tide it flows, together we weather wherever she goes! 🎶",
    "🎵 Raise up the sails and sing with me, hope rides high on the open sea! 🎵"
]
def get_shanty() -> str:
    """Return a random sea shanty or morale-boosting lyric."""
    return random.choice(SHANTIES)

JOKES = [
    "Why did the pirate get kicked off the ship? He couldn’t sea sharp!",
    "Why do programmers like the ocean? Because it’s full of C."
]
def get_joke() -> str:
    """Return a random crew joke."""
    return random.choice(JOKES)

# ── agent-profile loader ────────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parent.parent
PROFILES_DIR = BASE_DIR / "profiles"

def load_agent_profile(agent_id: str) -> dict:
    """
    Return profiles/<agent_id>.json as a dict.
    """
    path = PROFILES_DIR / f"{agent_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"profile {agent_id} missing at {path}")
    return json.loads(path.read_text(encoding="utf-8"))

try:
    from utils.smart_prompt_engine import build_smart_prompt
except ModuleNotFoundError:
    # Fallback: return empty prompt if the smart prompt engine is absent
    build_smart_prompt = lambda *args, **kwargs: ""

# ── APA citation formatter ─────────────────────────────────────────
def apa_format(author: str, year: str, title: str, source: str) -> str:
    """
    Format a citation according to APA 7th edition guidelines (simplified).
    Example: apa_format("Smith, J.", "2020", "The Art of Rituals", "Journal of Ritual Studies, 12(3), 45-59.")
    Returns: "Smith, J. (2020). The Art of Rituals. Journal of Ritual Studies, 12(3), 45-59."
    """
    return f"{author} ({year}). {title}. {source}"

# ── public re‑exports ─────────────────────────────────────────────
__all__ = [
    "semantic_search",
    "web_search",
    "get_pep_talk",
    "get_shanty",
    "get_joke",
    "load_agent_profile",
    "apa_format",
    "build_smart_prompt",
]
