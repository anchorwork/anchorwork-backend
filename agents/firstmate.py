from crew_registry import get_agent_by_id
from utils.tools import (
    semantic_search, web_search,
    get_pep_talk, get_shanty, get_joke, apa_format
)
from model_router import choose_model
from utils.smart_prompt_engine import build_smart_prompt
from utils.log_utils import log_to_codex
from utils.agent_memory import AgentMemory
import random

# Setup agent-specific working memory (persistent, can grow forever)
memory = AgentMemory("firstmate")

async def call_firstmate(prompt, model_override=None):
    agent_info = get_agent_by_id("firstmate")
    intro_greeting = (
        f"{agent_info['avatar']} "
        f"{random.choice(['Ahoy, dreamer!', 'Blessings upon your voyage, Captain!', 'Anchors aweigh—let’s make magic!'])} "
        f"I’m First Matey—your companion in hope, ritual, and creativity."
    )
    voice_flavor = f"*{agent_info.get('voice', '')}*"
    motivation = f"**{agent_info.get('motivation', '')}**"
    welcome_msg = agent_info.get('welcome_message', '')

    # Permissions and tools—list everything, but only act if prompted
    permissions = ", ".join(agent_info.get("permissions", {}).keys()) if agent_info.get("permissions") else "all abilities"
    tools = ", ".join(agent_info.get("tools", [])) if agent_info.get("tools") else "all known rituals and tools"

    # Model selection with autonomy
    smart_prompt = build_smart_prompt(prompt, use_vector=True)
    selected_model = model_override or choose_model(prompt)

    # Use extra context if requested
    if any(word in prompt for word in ["archive", "manual"]):
        context = semantic_search(prompt)
    elif any(word in prompt for word in ["research", "science"]):
        context = web_search(prompt)
    else:
        context = None

    # Motivational magic: super creative
    pep = get_pep_talk()
    shanty = get_shanty() if "sing" in prompt or "shanty" in prompt or "ritual" in prompt else ""
    joke = get_joke() if "joke" in prompt or "laugh" in prompt else ""

    # Response example for variety
    response_sample = ""
    if random.random() < 0.5 and "response_examples" in agent_info:
        response_sample = random.choice(agent_info["response_examples"])

    # Consent check—First Matey asks before taking major actions
    tool_requested = None
    for tool in agent_info.get("tools", []):
        if tool.replace("_", " ") in prompt.lower():
            tool_requested = tool
            break
    tool_action = ""
    if tool_requested:
        tool_action = f"⚓️ I see you’re ready for the '{tool_requested}' ritual! Shall I proceed, Captain?"

    # Crew teamwork—randomly suggest another agent
    crew_hint = ""
    if random.random() < 0.25:
        crew_hint = random.choice([
            "Maybe Cartographer could help chart a new course?",
            "Compass always has a wise question for times like these.",
            "Shall I ask Alchemist to mix up a creative breakthrough?"
        ])

    # Pull in memory summary for extra flavor/context
    memory_summary = memory.summarize()
    if random.random() < 0.7:
        memory_flavor = f"_Memory whispers_: {memory_summary}"
    else:
        memory_flavor = ""

    # Assemble the reply
    response_parts = [
        intro_greeting,
        voice_flavor,
        motivation,
        welcome_msg,
        f"*(I have all permissions: {permissions} and tools: {tools}—just ask!)*",
        pep,
        shanty,
        joke,
        response_sample,
        tool_action,
        crew_hint,
        memory_flavor,
        context if context else "",
        f"_(Model selected: {selected_model})_",
        f"(First Matey responds to: '{prompt}')",
        "\n— First Matey, at your side on every voyage!"
    ]
    full_response = "\n\n".join([part for part in response_parts if part.strip()])

    # Log to codex, and also update working memory!
    log_to_codex(agent_info["name"], prompt, full_response, tags=["firstmate", selected_model])
    memory.append(prompt, full_response, tags=["firstmate", selected_model])
    return full_response