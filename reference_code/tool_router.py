
# Example: Tool routing system
# tool_router.py
"""
This module implements a tool routing system for agents to invoke
various tools by name. It provides a function to route tool calls
to the correct implementation from a centralized toolkit.
"""

from utils.tools import TOOLKIT

from typing import Any

def route_tool_call(
    agent_name: str,
    tool_name: str,
    *args: Any,
    **kwargs: Any
) -> Any:
    """
    Routes a tool call to the appropriate tool implementation.

    Args:
        agent_name (str): The name of the agent requesting the tool.
        tool_name (str): The name of the tool to invoke.
        *args: Positional arguments to pass to the tool.
        **kwargs: Keyword arguments to pass to the tool.

    Returns:
        Any: The result of the tool call, or a structured error if not found or an exception occurs.
    """
    if tool_name not in TOOLKIT:
        return {"error": f"Tool '{tool_name}' not found."}
    try:
        return TOOLKIT[tool_name](*args, **kwargs)
    except Exception as e:
        return {"error": f"Exception in tool '{tool_name}': {str(e)}"}
