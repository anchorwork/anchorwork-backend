import os
import time
from typing import Dict

# Model environment variables and their purposes:
# MODEL_MAIN: The default general-purpose model.
# MODEL_CODER: Model specialized for coding tasks.
# MODEL_IMAGE: Model specialized for image generation tasks.
# MODEL_AUDIO: Model specialized for audio transcription and processing.
# MODEL_SEARCH: Model specialized for web search tasks.
# 
# Agent-specific models:
# MODEL_FIRST_MATE, MODEL_CARTOGRAPHER, MODEL_ALCHEMIST, MODEL_COMPASS, MODEL_WATCHER: 
#   Assigned to various agent roles, defaulting to MODEL_MAIN unless overridden.
# MODEL_RESEARCHER: Assigned to research-related agent tasks, defaults to MODEL_SEARCH.
#
# Routing logic in choose_model:
# 1. Check if the prompt contains an agent's name phrase and route to that agent's model.
# 2. Check for direct "switch to [model]" commands and switch accordingly.
# 3. Check for image-related keywords.
# 4. Check for audio-related keywords.
# 5. Check for search-related keywords.
# 6. Check for coding-related keywords.
# 7. Default to MODEL_MAIN.

MODEL_MAIN = os.getenv("MODEL_MAIN", "gpt-4o")
MODEL_CODER = os.getenv("MODEL_CODER", "codex-1")
MODEL_IMAGE = os.getenv("MODEL_IMAGE", "gpt-image-1")
MODEL_AUDIO = os.getenv("MODEL_AUDIO", "gpt-4o-mini-audio-preview")
MODEL_SEARCH = os.getenv("MODEL_SEARCH", "gpt-4o-search-preview")

MODEL_FIRST_MATE = os.getenv("MODEL_FIRST_MATE", MODEL_MAIN)
MODEL_CARTOGRAPHER = os.getenv("MODEL_CARTOGRAPHER", MODEL_MAIN)
MODEL_ALCHEMIST = os.getenv("MODEL_ALCHEMIST", MODEL_MAIN)
MODEL_COMPASS = os.getenv("MODEL_COMPASS", MODEL_MAIN)
MODEL_WATCHER = os.getenv("MODEL_WATCHER", MODEL_MAIN)
MODEL_RESEARCHER = os.getenv("MODEL_RESEARCHER", MODEL_SEARCH)

IMAGE_KEYWORDS = ["draw", "generate an image", "visual", "scene"]
AUDIO_KEYWORDS = ["transcribe", "audio", "recording", "voice note"]
SEARCH_KEYWORDS = ["search", "look up", "find on the web"]
CODER_KEYWORDS = ["debug", "fix", "code", "script", "function"]

AGENT_MODEL_KEYWORDS = {
    "first mate": MODEL_FIRST_MATE,
    "cartographer": MODEL_CARTOGRAPHER,
    "alchemist": MODEL_ALCHEMIST,
    "compass": MODEL_COMPASS,
    "watcher": MODEL_WATCHER,
    "researcher": MODEL_RESEARCHER,
}

ALL_MODELS = {
    MODEL_MAIN,
    MODEL_CODER,
    MODEL_IMAGE,
    MODEL_AUDIO,
    MODEL_SEARCH,
    MODEL_FIRST_MATE,
    MODEL_CARTOGRAPHER,
    MODEL_ALCHEMIST,
    MODEL_COMPASS,
    MODEL_WATCHER,
    MODEL_RESEARCHER,
}

AVAILABLE_MODELS = [
    "gpt-4.1-2025-04-14",
    "gpt-4.1-mini-2025-04-14",
    "gpt-4.1-mini (long context)",
    "o4-mini-2025-04-16",
    "o3-mini-2025-01-31",
    "gpt-4o"
]

CONFIRM_MODEL_SWITCH = True

def confirm_switch(model_name: str) -> bool:
    if not CONFIRM_MODEL_SWITCH:
        return True
    print(f"\n⚠️ Model switch requested to: {model_name}")
    confirm = input("Confirm switch? (y/n): ").strip().lower()
    return confirm == "y"

def list_available_models() -> None:
    print("\n🔍 Available models:")
    for model in AVAILABLE_MODELS:
        print(f"• {model}")

model_memory = {
    "current": MODEL_MAIN,
    "locked": False,
    "last_used": time.time()
}

def choose_model(task_type: str, token_estimate: int = 0) -> str:
    """
    Smart model chooser based on task type and token size.
    """
    # Default personality model
    if task_type == "chat":
        return "gpt-4.1-2025-04-14"
    
    # Long-form analysis or summaries
    if task_type == "scan" or token_estimate > 3000:
        return "gpt-4.1-mini-2025-04-14"

    # Code reasoning or structured planning
    if task_type in {"fix_plan", "code_reasoning"}:
        return "o4-mini-2025-04-16"

    # Lightweight generation or doc writing
    if task_type in {"docs", "tests", "checklist"}:
        return "o3-mini-2025-01-31"

    return "gpt-4.1-2025-04-14"  # fallback

def choose_model(prompt: str) -> str:
    """
    Choose the appropriate model based on the content of the prompt.

    Routing layers:
    1. If the model selection is locked, return the current model.
    2. Check if the prompt contains an agent's name phrase and route to that agent's model.
    3. Parse for direct "switch to [model]" commands and switch accordingly if model recognized.
    4. Check for image-related keywords.
    5. Check for audio-related keywords.
    6. Check for search-related keywords.
    7. Check for coding-related keywords.
    8. Default to MODEL_MAIN.

    Args:
        prompt (str): The input prompt string.

    Returns:
        str: The selected model name.
    """
    prompt_lower = prompt.lower()

    if model_memory.get("locked"):
        return model_memory["current"]

    # Check for agent keywords
    for agent_phrase, agent_model in AGENT_MODEL_KEYWORDS.items():
        if agent_phrase in prompt_lower:
            return agent_model

    # Check for direct switch commands: "switch to [model]"
    # We look for phrases like "switch to gpt-4o" or "switch to codex-1"
    # This is a simple substring check for "switch to " followed by model name
    switch_prefix = "switch to "
    if switch_prefix in prompt_lower:
        # Extract the part after "switch to "
        idx = prompt_lower.find(switch_prefix)
        after_switch = prompt_lower[idx + len(switch_prefix):].strip()
        # The model name is assumed to be the first word after "switch to "
        # but we allow for possible trailing punctuation or words, so we split by whitespace
        model_candidate = after_switch.split()[0] if after_switch else ""
        # Check if candidate matches any known model
        if model_candidate in ALL_MODELS:
            # Optionally lock the model on switch (not required, so just switch here)
            return model_candidate

    if any(keyword in prompt_lower for keyword in IMAGE_KEYWORDS):
        return MODEL_IMAGE
    if any(keyword in prompt_lower for keyword in AUDIO_KEYWORDS):
        return MODEL_AUDIO
    if any(keyword in prompt_lower for keyword in SEARCH_KEYWORDS):
        return MODEL_SEARCH
    if any(keyword in prompt_lower for keyword in CODER_KEYWORDS):
        return MODEL_CODER

    return MODEL_MAIN

def update_model_state(selected_model: str) -> None:
    """
    Update the current model state with the selected model and refresh the last used timestamp.

    Args:
        selected_model (str): The model name to set as current.
    """
    model_memory["current"] = selected_model
    model_memory["last_used"] = time.time()

def reset_to_main_if_idle(idle_minutes: int = 15) -> None:
    """
    Reset the current model to the main model if the system has been idle for a specified time.

    Args:
        idle_minutes (int, optional): The number of minutes of inactivity before reset. Defaults to 15.
    """
    now = time.time()
    if not model_memory.get("locked") and (now - model_memory["last_used"]) > idle_minutes * 60:
        model_memory["current"] = MODEL_MAIN

def lock_model(model_name: str) -> None:
    """
    Lock the model selection to a specific model.

    Args:
        model_name (str): The model name to lock.
    """
    model_memory["current"] = model_name
    model_memory["locked"] = True
    model_memory["last_used"] = time.time()

def unlock_model() -> None:
    """
    Unlock the model selection, allowing automatic model switching.
    """
    model_memory["locked"] = False
    model_memory["last_used"] = time.time()

def get_model_state() -> Dict[str, object]:
    """
    Get a copy of the current model state.

    Returns:
        Dict[str, object]: A copy of the model memory dictionary.
    """
    return model_memory.copy()
