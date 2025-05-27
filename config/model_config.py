# config/model_config.py
"""
Central model registry + env-driven defaults.

This module defines a registry of models used by various agents and tasks,
with environment variable overrides and safe defaults. It provides functions
to ensure models are registered and to retrieve default models for agents.
"""

import os

MODEL_REGISTRY = {
    "gpt-4o-mini": {
        "context": 32_000,
        "speed":   "💨",
        "cost":    "low",
        "notes":   "routing / meta",
    },
    "gpt-4o-2024-11-20": {
        "context": 128_000,
        "speed":   "fast",
        "cost":    "med",
        "notes":   "balanced default",
    },
    "gpt-4.1-long": {
        "context": 200_000,
        "speed":   "slow",
        "cost":    "high",
        "notes":   "huge ctx",
    },
}

def _ensure(mid: str):
    """
    Ensure that a model ID exists in the MODEL_REGISTRY.
    If not present, add a placeholder entry with default unknown values.
    """
    if mid not in MODEL_REGISTRY:
        MODEL_REGISTRY[mid] = {
            "context": 0, "speed": "?", "cost": "?", "notes": "from .env"
        }

# Load main and agent-specific models from environment variables with safe defaults
MODEL_MAIN        = os.getenv("MODEL_MAIN",        "gpt-4o-2024-11-20")
MODEL_CODER       = os.getenv("MODEL_CODER",       MODEL_MAIN)
MODEL_FIRST_MATE  = os.getenv("MODEL_FIRST_MATE",  MODEL_MAIN)
MODEL_CARTOGRAPHER= os.getenv("MODEL_CARTOGRAPHER", "gpt-4.1-long")
MODEL_ALCHEMIST   = os.getenv("MODEL_ALCHEMIST",   MODEL_MAIN)
MODEL_COMPASS     = os.getenv("MODEL_COMPASS",     MODEL_MAIN)
MODEL_WATCHER     = os.getenv("MODEL_WATCHER",     MODEL_MAIN)
MODEL_RESEARCHER  = os.getenv("MODEL_RESEARCHER",  MODEL_MAIN)

# Models for specialized tasks
MODEL_IMAGE       = os.getenv("MODEL_IMAGE",       "dall-e-3")
MODEL_AUDIO       = os.getenv("MODEL_AUDIO",       "whisper-1")
MODEL_SEARCH      = os.getenv("MODEL_SEARCH",      "bing-chat")
EMBED_MODEL       = os.getenv("EMBED_MODEL",       "text-embedding-3-large")

# Optional fallback models if defined in environment
FALLBACK_MODEL_1  = os.getenv("FALLBACK_MODEL_1")
FALLBACK_MODEL_2  = os.getenv("FALLBACK_MODEL_2")

# Ensure all models are registered in the MODEL_REGISTRY
for _mid in (
    MODEL_MAIN,
    MODEL_CODER,
    MODEL_FIRST_MATE,
    MODEL_CARTOGRAPHER,
    MODEL_ALCHEMIST,
    MODEL_COMPASS,
    MODEL_WATCHER,
    MODEL_RESEARCHER,
    MODEL_IMAGE,
    MODEL_AUDIO,
    MODEL_SEARCH,
    EMBED_MODEL,
):
    _ensure(_mid)

if FALLBACK_MODEL_1:
    _ensure(FALLBACK_MODEL_1)
if FALLBACK_MODEL_2:
    _ensure(FALLBACK_MODEL_2)

def describe_model(mid: str) -> str:
    """
    Return a short description string for the given model ID.
    """
    return f"{mid} · {MODEL_REGISTRY[mid]['notes']}"

def get_default_model(agent_id: str = "main") -> str:
    """
    Retrieve the default model ID for a given agent ID.

    Supported agent IDs:
        - main
        - coder
        - first_mate
        - cartographer
        - alchemist
        - compass
        - watcher
        - researcher
        - image
        - audio
        - search
        - embed

    Returns the model ID string or falls back to MODEL_MAIN if unknown.
    """
    return {
        "main":         MODEL_MAIN,
        "coder":        MODEL_CODER,
        "first_mate":   MODEL_FIRST_MATE,
        "cartographer": MODEL_CARTOGRAPHER,
        "alchemist":    MODEL_ALCHEMIST,
        "compass":      MODEL_COMPASS,
        "watcher":      MODEL_WATCHER,
        "researcher":   MODEL_RESEARCHER,
        "image":        MODEL_IMAGE,
        "audio":        MODEL_AUDIO,
        "search":       MODEL_SEARCH,
        "embed":        EMBED_MODEL,
    }.get(agent_id.lower(), MODEL_MAIN)
