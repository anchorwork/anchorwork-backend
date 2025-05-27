# utils/reference_builder.py

from utils.openai_caller import call_gpt
from utils.web_search import web_search
from pathlib import Path
from datetime import datetime
from typing import Tuple, Union

def build_reference(topic: str, use_web: bool = True) -> Tuple[str, Union[str, None]]:
    """
    Builds a Markdown (.md) and Python (.py) reference file for a given topic.

    Parameters:
        topic (str): The subject to build the reference guide for.
        use_web (bool): Whether to include web search results in the reference.

    Returns:
        Tuple[str, Union[str, None]]: Paths to the generated Markdown file and Python file,
        or a message indicating no Python file was generated.
    """
    header = f"# Reference Guide: {topic}\n\nGenerated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    body = ""

    if use_web:
        web_results = web_search(topic)
        body += "## Web Summary\n"
        body += web_results
        body += "\n\n"

    gpt_instruction = (
        f"Write a reference guide and code example for the topic '{topic}'. "
        "Begin with a brief explanation in Markdown, followed by a clear Python code block."
    )
    gpt_response = call_gpt(gpt_instruction, model="gpt-4")
    body += gpt_response

    # Save .md
    ref_md_path = Path("reference_code") / f"{topic.replace(' ', '_').lower()}.md"
    ref_md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ref_md_path, "w") as f:
        f.write(header + body)

    ref_py_path = None
    # Attempt to extract code and save separately
    try:
        code_block = gpt_response.split("```python")[1].split("```")[0].strip()
        ref_py_path = Path("reference_code") / f"{topic.replace(' ', '_').lower()}.py"
        with open(ref_py_path, "w") as f:
            f.write(code_block)
    except Exception:
        code_block = None  # No code block extracted

    if ref_py_path is not None:
        return str(ref_md_path), str(ref_py_path)
    else:
        return str(ref_md_path), "No Python file generated."
