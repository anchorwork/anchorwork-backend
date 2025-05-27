# agents/cartographer.py

from utils.smart_prompt_engine import build_smart_prompt
from model_router import choose_model
from utils.log_utils import log_to_codex
from crew_registry import get_agent_by_id
from utils.agent_memory import AgentMemory

memory = AgentMemory("cartographer")

import random

async def call_cartographer(prompt, model_override=None):
    agent_info = get_agent_by_id("cartographer")
    personality_intro = random.choice([
        "🗺️ Let me chart a course for your idea.",
        "As your trusted Cartographer, I'm opening my logbook...",
        "Time to draft new territory on your creative map!"
    ])

    # Build a context-rich prompt
    smart_prompt = build_smart_prompt(prompt, use_vector=True)
    selected_model = model_override or choose_model(prompt)

    # TODO: Replace the next line with your AI/model call logic
    # For now, we'll mock a response
    ai_response = f"(Long-form structure/plan for: '{prompt}')"

    memory_summary = memory.summarize()
    memory_flavor = f"_Cartographer recalls_: {memory_summary}" if memory_summary else ""

    # Add personality/quirk: references explorers, logbook, etc.
    closing = "\n\n— Cartographer, logging new discoveries for Anchorwork."
    
    full_response = f"{personality_intro}\n\n{ai_response}\n\n{memory_flavor}{closing}"

    # Log this action (optional tags for traceability)
    log_to_codex(
        agent_info["name"], prompt, full_response,
        tags=["structure", "planning", selected_model]
    )
    memory.append(prompt, full_response, tags=["cartographer", selected_model])
    return full_response
