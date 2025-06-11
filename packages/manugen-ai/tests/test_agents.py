"""
Tests for various agents
"""

from manugen_ai.agents.repo_to_paper.agent import root_agent
from manugen_ai.utils import run_agent_workflow
import pytest
import pathlib


@pytest.mark.asyncio
async def test_something(temp_markdown_dir: pathlib.Path):
    APP_NAME = "db_tool_app"
    USER_ID = "repo_to_paper_user"
    SESSION_ID = "session_0001"
    final_output, session_state, output_events = await run_agent_workflow(
        agent=root_agent,
        prompt="""
        Please turn this repository into a scientific paper abstract and revise it within a loop.
        https://github.com/manubot/manubot-ai-editor
        """,
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        initial_state={
            "repository_url": "https://github.com/manubot/manubot-ai-editor",
            "content_path": str(temp_markdown_dir.resolve()),
        },
        # note: use `uv run pytest -s` to view the verbose stdout
        verbose=True,
    )
    # assert we have an abstract which was added
    assert "abstract" in session_state.keys()


import nbformat
from nbclient import NotebookClient
from pathlib import Path
import pytest


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


def get_cell_outputs(nb: nbformat.NotebookNode) -> list[str]:
    outputs = []
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            text = ""
            if output.output_type == "stream":
                text = output.get("text", "")
            elif output.output_type == "execute_result":
                text = output.get("data", {}).get("text/plain", "")
            elif output.output_type == "display_data":
                text = output.get("data", {}).get("text/plain", "")
            if text:
                outputs.append(text.strip())
    return outputs


@pytest.mark.parametrize(
    "notebook_path",
    [
        ("tests/reports/run_agent.ipynb"),
    ],
)
def test_notebook_outputs_match(tmp_path, notebook_path, reference_path):
    executed = run_notebook(
        input_path=pathlib.Path(notebook_path),
        output_path=(new_path := tmp_path / "temp_path"),
    )
    reference = nbformat.read(Path(new_path), as_version=4)

    executed_outputs = get_cell_outputs(executed)
    reference_outputs = get_cell_outputs(reference)

    assert executed_outputs == reference_outputs, (
        "Notebook output mismatch:\n"
        f"Expected:\n{reference_outputs}\n\nGot:\n{executed_outputs}"
    )
