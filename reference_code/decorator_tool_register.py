
"""
Tool Registry Module
-------------------

This module provides a registry for tools (functions) using a decorator pattern.
Tools can be registered with a unique name and later retrieved by name.
Includes:
- `register_tool`: Decorator to register a function as a tool.
- `get_tool`: Function to retrieve a registered tool by name.
"""

# Example: Registering a tool using a decorator

TOOL_REGISTRY = {}

from typing import Callable, Any

def register_tool(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to register a function as a tool with a given name.
    Warns if a tool with the same name is already registered.
    """
    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        if name in TOOL_REGISTRY:
            print(f"Warning: Tool '{name}' is already registered and will be overwritten.")
        TOOL_REGISTRY[name] = func
        return func
    return wrapper

@register_tool("say_hello")
def say_hello() -> str:
    """
    Returns a friendly greeting.
    """
    return "Hello, Captain!"


def get_tool(name: str) -> Callable[..., Any]:
    """
    Retrieve a registered tool by name.
    Raises KeyError if the tool does not exist.
    """
    try:
        return TOOL_REGISTRY[name]
    except KeyError:
        raise KeyError(f"Tool '{name}' is not registered. Available tools: {list(TOOL_REGISTRY.keys())}")


if __name__ == "__main__":
    # Example usage:
    tool = get_tool("say_hello")
    print(tool())  # Should print: Hello, Captain!
