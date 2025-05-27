# Example: Using pathlib for cross-platform file handling

from pathlib import Path
from typing import Union, List

def list_code_files(folder: Union[str, Path] = "anchorwork", as_path: bool = False) -> List[Union[str, Path]]:
    """
    List all Python (.py) files in the given folder and its subfolders.

    Args:
        folder (Union[str, Path]): The folder to search in. Defaults to "anchorwork".
        as_path (bool): If True, return a list of Path objects; otherwise, return a list of strings. Defaults to False.

    Returns:
        List[Union[str, Path]]: List of Python file paths as strings or Path objects.
    """
    folder_path = Path(folder)
    files = list(folder_path.rglob("*.py"))
    if as_path:
        return files
    else:
        return [str(p) for p in files]
