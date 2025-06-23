"""
Tools for agents within manugen-ai
"""

from __future__ import annotations

import json
import pathlib
import tempfile
from typing import Any, Dict, List

import pygit2
import requests
from google.adk.tools.tool_context import ToolContext
from jsonschema import ValidationError, validate
from manugen_ai.utils import graceful_fail
from pyalex import Works


@graceful_fail()
def parse_list(text: str) -> List[str]:
    """
    Convert newline- or bullet-separated
    text into a list of strings.

    Args:
        text (str):
            Text containing newline-
            or bullet-separated lines.

    Returns:
        List[str]:
            A list of cleaned string items,
            with bullets or numbering removed.
    """
    lines = text.splitlines()
    items = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        # remove leading bullets or numbering
        for prefix in ("-", "*"):
            if ln.startswith(prefix):
                ln = ln.lstrip(prefix).strip()
        items.append(ln)
    return items


@graceful_fail()
def openalex_query(topics: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    For each topic, search OpenAlex and return only
    title and abstract for open-access works.

    Args:
        topics (str):
            Topics to search for, as a string.

    Returns:
        Dict[str, List[Dict[str, Any]]]:
            Mapping from topic to list of dicts with
            'title' and 'abstract'.
    """
    client = Works()
    limit = 3

    works = (
        # search by abstracts with topics
        client.search_filter(abstract=topics)
        # filter retractions
        .filter(is_retracted=False)
        # sort descending by citation count
        .sort(cited_by_count="desc")
        # set a limit to our results
        .get(per_page=limit)
    )
    output = [
        # return only title, abstract, and DOI
        {"title": w["title"], "abstract": w["abstract"], "doi": w["doi"]}
        for w in works
    ]

    return output


@graceful_fail()
def exit_loop(tool_context: ToolContext):
    """
    Call this function ONLY when the critique
    indicates no further changes are needed,
    signaling the iterative process should end.
    """
    print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")  # noqa: T201
    tool_context.actions.escalate = True
    # Return empty dict as tools should typically return JSON-serializable output
    return {}


@graceful_fail()
def fetch_url(url: str) -> str:
    """
    Fetch the text content of a web resource.

    Args:
        url: URL to retrieve.

    Returns:
        str: Content of the URL.
    """
    res = requests.get(url)
    res.raise_for_status()
    return res.text


@graceful_fail()
def json_conforms_to_schema(raw: str, schema: dict) -> bool:
    """
    Check whether a JSON string conforms
    to a given JSON Schema.

    Parses the input string as JSON,
    then validates it against the provided schema.

    Args:
        raw:
            A JSON-formatted string to validate.
        schema:
            A JSON Schema (as a dict-like
            mapping) that `raw` must conform to.

    Returns:
        True if `raw` is valid JSON and
        satisfies `schema`; False otherwise.
    """
    try:
        data: Any = json.loads(raw)
        validate(instance=data, schema=schema)
    except (json.JSONDecodeError, ValidationError):
        return False
    return True


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
        return fp.stat().st_size <= 250_000 and fp.suffix in {
            ".md",
            ".txt",
            ".py",
            ".java",
            ".R",
            ".json",
            ".yaml",
            ".yml",
            ".html",
            ".css",
            ".js",
            ".ts",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
        }

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
    # ensure the path exists
    repo_path.mkdir(parents=True, exist_ok=True)
    # Clone the repository from the given URL into the defined path
    pygit2.clone_repository(repo_url, str(repo_path))

    return str(repo_path)
