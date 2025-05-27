"""
Anchorwork Crew Brainstorm Orchestrator
---------------------------------------
Runs a multi-agent brainstorm/council session—inviting every crew member to respond with their own memory, voice, and creative flair.

Extensible for crew voting, ritual synthesis, and cross-agent commentary.
"""

import asyncio

# Import your agent callables (make sure paths match your project structure)
from agents.firstmate import call_firstmate
from agents.cartographer import call_cartographer
from agents.compass import call_compass
from agents.watcher import summarize_logs
from agents.alchemist import call_alchemist
from agents.coder import Coder
from crew_registry import crew_registry, get_agent_by_id

# If Coder requires instantiation, instantiate here
coder_agent = Coder(profile={})

# Map agent IDs to their main callable functions
AGENT_CALLS = {
    "firstmate": call_firstmate,
    "cartographer": call_cartographer,
    "compass": call_compass,
    "watcher": summarize_logs,        # expects a keyword, so may need tweaking
    "alchemist": call_alchemist,
    "coder": coder_agent.handle_prompt,  # If handle_prompt is async; if not, wrap with asyncio.to_thread
}

async def run_crew_brainstorm(prompt: str) -> dict:
    """
    Orchestrate a brainstorm: prompt every crew agent for their response.
    Returns a dict {agent_name: agent_response}
    """
    results = {}

    for agent in crew_registry:
        call_fn = AGENT_CALLS.get(agent["id"])
        if not call_fn:
            continue

        # Special handling: Watcher expects a 'keyword', not a general prompt.
        if agent["id"] == "watcher":
            # Use the prompt or extract a key word.
            watcher_response = await call_fn(prompt)
            results[agent["name"]] = watcher_response
        elif agent["id"] == "coder":
            # Coder's handle_prompt may not be async; wrap in thread if needed
            try:
                coder_response = await asyncio.to_thread(call_fn, prompt)
            except Exception:
                coder_response = call_fn(prompt)
            results[agent["name"]] = coder_response
        else:
            agent_response = await call_fn(prompt)
            results[agent["name"]] = agent_response

    return results

def format_crew_brainstorm_output(results: dict) -> str:
    """
    Nicely formats all agent responses into a single readable block.
    """
    formatted = ["🪶 **Anchorwork Crew Council Brainstorm** 🪶\n"]
    for name, response in results.items():
        formatted.append(f"\n---\n**{name} says:**\n{response}")
    formatted.append("\n---\nCrew council complete. What will you try next, Captain?")
    return "\n".join(formatted)

# Synchronous helper for convenience (if running outside an async context)
def crew_brainstorm(prompt: str) -> str:
    results = asyncio.run(run_crew_brainstorm(prompt))
    return format_crew_brainstorm_output(results)

# Example usage
if __name__ == "__main__":
    test_prompt = "I need a ritual for resetting my energy after a stressful week."
    print(crew_brainstorm(test_prompt))