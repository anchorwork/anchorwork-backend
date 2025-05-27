"""
Anchorwork Council UI Tools
---------------------------
Handles the formatting and (optionally) interaction for multi-agent council sessions.
Adapts output for terminal, log, or app front-end.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from typing import Dict

# If you want, import agent avatars or moods here!
from crew_registry import crew_registry

console = Console()

def display_council_responses(responses: Dict[str, str]):
    """
    Prints each agent's response in a stylized panel.
    """
    console.print("[bold magenta]\nAnchorwork Crew Council Results[/bold magenta]")
    for agent in crew_registry:
        name = agent["name"]
        avatar = agent.get("avatar", "")
        mood = agent.get("mood", "steady")
        response = responses.get(name, "")
        header = f"{avatar} [bold blue]{name}[/bold blue] — [italic]{mood}[/italic]"
        panel = Panel(Text(response, justify="left"), title=header, border_style="cyan")
        console.print(panel)
    console.print("[green]Council complete. What will you try next, Captain?[/green]")

def display_council_table(responses: Dict[str, str]):
    """
    Displays all responses in a single table.
    """
    table = Table(title="Anchorwork Crew Council Table")
    table.add_column("Agent", justify="center", style="bold")
    table.add_column("Avatar", justify="center")
    table.add_column("Mood", justify="center")
    table.add_column("Response", justify="left")
    for agent in crew_registry:
        name = agent["name"]
        avatar = agent.get("avatar", "")
        mood = agent.get("mood", "steady")
        response = responses.get(name, "")
        table.add_row(name, avatar, mood, response)
    console.print(table)

# Example interactive prompt (for future use)
def council_decision_prompt(options):
    """
    Presents decision options and gets user input.
    """
    console.print("\n[bold]The crew has offered several suggestions. Which will you choose?[/bold]")
    for idx, option in enumerate(options, 1):
        console.print(f"{idx}. {option}")
    choice = console.input("[blue]Enter your choice number: [/blue]")
    try:
        idx = int(choice) - 1
        return options[idx]
    except (ValueError, IndexError):
        console.print("[red]Invalid choice. Try again.[/red]")
        return council_decision_prompt(options)

# Example usage for demo
if __name__ == "__main__":
    mock_responses = {
        "First Matey": "Let's sing a restorative shanty!",
        "Cartographer": "Let's map your next adventure.",
        "Alchemist": "A color-changing tea ritual for transformation.",
        "Compass": "Check your true north—what matters most?",
        "Watcher": "Your stress peaks midweek. Let's watch for that.",
        "Coder": "Automate check-ins for self-care."
    }
    display_council_responses(mock_responses)
    display_council_table(mock_responses)