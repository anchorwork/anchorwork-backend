"""
Anchorwork Agent Interaction Engine
-----------------------------------
Facilitates conversations, commentary, and collaboration between multiple Anchorwork agents.
Use for agent-to-agent feedback, debate, or group ritual-building.

Future expansions: agent voting, agent “roundtable,” consensus generation, and AI-powered crew chat simulations.
"""

from crew_registry import crew_registry, get_agent_by_id

def agent_comment_on_agent(commenting_agent_id: str, target_agent_id: str, last_prompt: str, last_response: str) -> str:
    """
    Generate a commentary or feedback message from one agent about another agent's latest action.
    This is the start of cross-agent dialogue!
    """
    commenting_agent = get_agent_by_id(commenting_agent_id)
    target_agent = get_agent_by_id(target_agent_id)
    # Example flavor: Use each agent’s voice for the comment
    voice_flavor = commenting_agent.get("voice", "")
    # Creative template:
    comment = (
        f"As {commenting_agent['name']} ({voice_flavor}), responding to {target_agent['name']}:\n"
        f"'{last_response[:200]}...'\n"
        f"My thoughts: "
    )
    # Playful, improvisational example:
    if commenting_agent["id"] == "firstmate":
        comment += "A hearty cheer for your insight! Shall we set sail on this idea, or tighten the ropes a bit?"
    elif commenting_agent["id"] == "cartographer":
        comment += "I see the contours of a promising route. Shall I chart the next phase?"
    elif commenting_agent["id"] == "alchemist":
        comment += "Let’s mix in a drop of wonder—this could become a whole new elixir!"
    elif commenting_agent["id"] == "coder":
        comment += "I’d refactor this with a bit of code magic, but the spirit’s true!"
    elif commenting_agent["id"] == "compass":
        comment += "This aligns beautifully with our guiding values."
    elif commenting_agent["id"] == "watcher":
        comment += "I observe a pattern: this approach has weathered many storms."
    else:
        comment += "I add my own unique perspective to the mix!"
    return comment

def run_agent_commentary_round(prompt: str, responses: dict) -> dict:
    """
    For every agent, have them comment on another agent’s last response.
    Returns a dict {commenting_agent_name: commentary}
    """
    commentary = {}
    agent_ids = [agent["id"] for agent in crew_registry]
    for i, commenting_agent_id in enumerate(agent_ids):
        # Each agent comments on the previous agent in the list (circular)
        target_agent_id = agent_ids[i - 1] if i > 0 else agent_ids[-1]
        last_prompt = prompt
        last_response = responses.get(get_agent_by_id(target_agent_id)["name"], "")
        comment = agent_comment_on_agent(commenting_agent_id, target_agent_id, last_prompt, last_response)
        commentary[get_agent_by_id(commenting_agent_id)["name"]] = comment
    return commentary

# Example for future extension: agent voting, ritual co-authorship, or dialogue simulation

if __name__ == "__main__":
    # Mock prompt and agent responses for demonstration
    mock_prompt = "How do we help the user handle burnout?"
    mock_responses = {
        "First Matey": "Let's sing a restorative shanty and celebrate small victories!",
        "Cartographer": "I suggest mapping the user's energy patterns to plan restful rituals.",
        "Alchemist": "How about a color-changing tea ceremony for transformation?",
        "Coder": "I can automate daily check-ins to track self-care.",
        "Compass": "We should ensure all advice is rooted in the user's core values.",
        "Watcher": "The user seems to face stress spikes midweek—let's watch those patterns."
    }
    comments = run_agent_commentary_round(mock_prompt, mock_responses)
    for agent, comment in comments.items():
        print(f"\n{agent}'s commentary:\n{comment}")