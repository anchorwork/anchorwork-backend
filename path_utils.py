"""Utility functions for constructing file paths."""

from pathlib import Path

def get_path(filename: str, subfolder: str = "") -> str:
    """
    Construct an absolute file path.

    Args:
        filename (str): The name of the file.
        subfolder (str, optional): The subfolder within the base directory. Defaults to "".

    Returns:
        str: The absolute path to the file as a string.
    """
    base = Path(__file__).resolve().parent
    if subfolder:
        return str(base / subfolder / filename)
    return str(base / filename)
