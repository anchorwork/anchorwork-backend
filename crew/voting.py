"""
Anchorwork Crew Agent Voting System
-----------------------------------
Allows agents to vote on proposals, suggestions, or actions.
Supports tallying, weighted voting, consensus detection, and fun commentary.
"""

from crew_registry import crew_registry, get_agent_by_id
import random

def agent_vote(agent_id: str, options: list) -> int:
    """
    Simulate an agent voting for one of the given options.
    Returns the index of the chosen option.
    """
    agent = get_agent_by_id(agent_id)
    # You can add more complex logic based on agent mood, role, or past memory.
    # For now, pick randomly for demo purposes:
    choice = random.randint(0, len(options) - 1)
    return choice

def run_crew_vote(options: list) -> dict:
    """
    Collects votes from all agents for the provided options.
    Returns a dict {agent_name: index_of_choice}.
    """
    votes = {}
    agent_ids = [agent["id"] for agent in crew_registry]
    for agent_id in agent_ids:
        idx = agent_vote(agent_id, options)
        agent = get_agent_by_id(agent_id)
        votes[agent["name"]] = idx
    return votes

def tally_votes(votes: dict) -> dict:
    """
    Counts the total votes for each option.
    Returns a dict {option_index: vote_count}.
    """
    tally = {}
    for idx in votes.values():
        tally[idx] = tally.get(idx, 0) + 1
    return tally

def format_vote_results(options: list, votes: dict) -> str:
    """
    Formats the voting outcome for display.
    """
    tally = tally_votes(votes)
    lines = ["\n🎲 [bold]Crew Voting Results[/bold]\n"]
    for i, option in enumerate(options):
        count = tally.get(i, 0)
        agent_names = [agent for agent, idx in votes.items() if idx == i]
        lines.append(f"{i+1}. {option} — [green]{count} votes[/green] ([italic]{', '.join(agent_names)}[/italic])")
    # Find the top choice(s)
    max_votes = max(tally.values())
    winners = [options[i] for i, v in tally.items() if v == max_votes]
    lines.append(f"\n[bold cyan]Winner(s):[/bold cyan] {', '.join(winners)}")
    return "\n".join(lines)

# Example for demo:
if __name__ == "__main__":
    proposals = [
        "Host a group gratitude ritual tonight",
        "Run a creative brainstorming session",
        "Take a day for rest and quiet reflection",
        "Design a crew badge for emotional courage"
    ]
    votes = run_crew_vote(proposals)
    result_text = format_vote_results(proposals, votes)
    print(result_text)