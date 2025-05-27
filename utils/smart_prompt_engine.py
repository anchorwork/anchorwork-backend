import os
from typing import Union
from utils.semantic_search import semantic_search
from utils.web_search import web_search

def build_smart_prompt(prompt: str, use_vector: bool = True, use_web: bool = True) -> str:
    """
    Build a smart prompt by incorporating context from semantic search and recent web search results.

    Args:
        prompt (str): The user's input prompt.
        use_vector (bool): Whether to include context from semantic search.
        use_web (bool): Whether to include recent web search results.

    Returns:
        str: The combined prompt with context and user request.
    """
    context_parts = []

    if use_vector:
        vector_matches = semantic_search(prompt)
        if isinstance(vector_matches, str):
            # Handle error case where semantic_search returns a string error message
            context_parts.append("Anchorwork context from your archive:\n" + vector_matches)
        else:
            context_parts.append("Anchorwork context from your archive:\n" + "\n---\n".join(vector_matches))

    if use_web:
        web_text = web_search(prompt)
        context_parts.append("Recent research findings:\n" + web_text)

    full_prompt = "\n\n".join(context_parts) + f"\n\nUser request:\n{prompt}"
    return full_prompt
