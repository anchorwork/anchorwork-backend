
# utils/file_utils.py

from pathlib import Path
from typing import Any

def read_project_file(agent: Any, path: str) -> str:
    """
    Read the contents of a file at the given path if the agent has permission.
    Returns the file content as a string, or an error message string.
    """
    if not agent.has_permission("read_files"):
        return "Access denied: Agent cannot read files."
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def save_modified_file(agent: Any, original_path: str, content: str) -> str:
    """
    Save the modified content to a file in the agent_outputs directory,
    maintaining the relative path from 'anchorwork'. Returns the path to the saved file as a string,
    or an error message string.
    """
    if not agent.has_permission("write_to_agent_outputs"):
        return "Access denied: Agent cannot write output."

    try:
        rel_path = Path(original_path).relative_to("anchorwork")
    except Exception as e:
        return f"Error: The file path '{original_path}' is not under the 'anchorwork' directory. Details: {e}"
    base = Path("agent_outputs") / rel_path
    try:
        base.parent.mkdir(parents=True, exist_ok=True)
        with open(base, "w", encoding="utf-8") as f:
            f.write(content)
        return str(base)
    except Exception as e:
        return f"Error writing file: {e}"
