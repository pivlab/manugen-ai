"""
utilities for testing
"""

from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient


def run_notebook(
    input_path: Path,
    output_path: Path = None,
) -> nbformat.NotebookNode:
    """Execute a notebook and optionally write the result to a new file.

    Args:
        input_path (Path): Path to the source .ipynb file.
        output_path (Path, optional): If provided, write the executed notebook
            to this path. If None, result is not saved to disk.

    Returns:
        nbformat.NotebookNode: The executed notebook object.
    """
    with input_path.open(encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    client = NotebookClient(nb, timeout=600, kernel_name="python3")
    client.execute()

    if output_path:
        with output_path.open("w", encoding="utf-8") as f:
            nbformat.write(nb, f)

    return nb