"""
Tools for agents within manugen-ai
"""

from __future__ import annotations

import json
import pathlib
import tempfile
from typing import Any, Dict, List, Optional

import pygit2
import requests
from docling.document_converter import DocumentConverter
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
def openalex_query(
    topics: List[str],
    limit: int = 2,
    fields: Optional[List[str]] = None,
    fetch_fulltext: bool = False,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    For each topic, search OpenAlex and return minimal metadata,
    optionally downloading the open-access full text.

    Args:
        topics (List[str]):
            Search strings for which to find works.
        limit (int, optional):
            Number of works to retrieve per topic. Defaults to 2.
        fields (List[str], optional):
            Metadata fields to include. Defaults to ['title', 'abstract', 'best_oa_location'].
        fetch_fulltext (bool, optional):
            If True, attempts to download the open-access full text from
            each record's best_oa_location URL and adds it as 'fulltext'.

    Returns:
        Dict[str, List[Dict[str, Any]]]:
            Mapping of topic → list of dicts containing specified fields,
            '_id', '_doi', and optionally 'fulltext'.
    """

    if fields is None:
        fields = ["title", "abstract", "best_oa_location"]

    output: Dict[str, List[Dict[str, Any]]] = {}
    client = Works()

    for topic in topics:
        works = client.search(topic).get(per_page=limit)
        topic_results: List[Dict[str, Any]] = []

        for w in works:
            rec: Dict[str, Any] = {}
            for f in fields:
                rec[f] = w.get(f) if isinstance(w, dict) else getattr(w, f, None)
            rec["_id"] = w.get("id") if isinstance(w, dict) else None
            rec["_doi"] = w.get("doi") if isinstance(w, dict) else None

            # Attempt to fetch full text if requested
            if fetch_fulltext and rec.get("best_oa_location"):
                # best_oa_location may be a dict with 'url'
                oa = rec["best_oa_location"]
                url = oa.get("pdf_url") if isinstance(oa, dict) else None
                if url:
                    try:
                        doc = DocumentConverter().convert(url).document
                        rec["fulltext"] = doc.text
                    except Exception:
                        rec["fulltext"] = None

            topic_results.append(rec)

        output[topic] = topic_results

    return output


@graceful_fail()
def exit_loop(tool_context: ToolContext):
    """
    Call this function ONLY when the critique
    indicates no further changes are needed,
    signaling the iterative process should end.
    """
    print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    # Return empty dict as tools should typically return JSON-serializable output
    return {}


@graceful_fail()
def fetch_url(url: str) -> str:
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
    # ensure the path exists
    repo_path.mkdir(parents=True, exist_ok=True)
    # Clone the repository from the given URL into the defined path
    pygit2.clone_repository(repo_url, str(repo_path))

    return str(repo_path)
