"""
Tools for agents within manugen-ai
"""

from __future__ import annotations
import pathlib
import tempfile

import pygit2

from google.adk.tools.tool_context import ToolContext


def exit_loop(tool_context: ToolContext):
    """Call this function ONLY when the critique indicates no further changes are needed,
    signaling the iterative process should end."""
    print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    # Return empty dict as tools should typically return JSON-serializable output
    return {}


def read_path_contents(path: str) -> str:
    """
    Return a prompt-ready string that concatenates the contents of *path*.

    * If *path* is a file → read it directly.
    * If *path* is a directory → read each file.
      to parse every text-like file (Markdown, Python, JSON, …) **recursively**.
    Large/binary files are skipped so the response stays LLM-friendly.
    """
    p = pathlib.Path(path).expanduser().resolve()

    def is_text_file(fp: pathlib.Path) -> bool:
        return fp.stat().st_size <= 250_000

    files = []
    if p.is_file():
        files = [p] if is_text_file(p) else []
    elif p.is_dir():
        files = [fp for fp in p.rglob("*") if fp.is_file() and is_text_file(fp)]
    else:
        raise FileNotFoundError(f"{p} is neither a file nor a directory")

    contents = []
    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
            if text.strip():
                contents.append(text.strip())
        except Exception:
            continue  # skip unreadable/binary files

    return "\n\n".join(contents)


def clone_repository(repo_url: str) -> str:
    """
    Clones the GitHub repository to a temporary directory.

    Args:
        repo_url (str): The URL of the GitHub repository.

    Returns:
        str: Path to the cloned repository.
    """
    # Create a temporary directory to store the cloned repository
    temp_dir = tempfile.mkdtemp()
    # Define the path for the cloned repository within the temporary directory
    repo_path = pathlib.Path(temp_dir) / "repo"
    # Clone the repository from the given URL into the defined path
    pygit2.clone_repository(repo_url, str(repo_path))

    return str(repo_path)
