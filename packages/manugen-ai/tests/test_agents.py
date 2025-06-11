"""
Tests for various agents
"""

import pathlib

import pytest
from manugen_ai.agents.repo_to_paper.agent import root_agent
from manugen_ai.utils import run_agent_workflow

from tests.utils import run_notebook


@pytest.mark.asyncio
async def test_agent_output(temp_markdown_dir: pathlib.Path):
    APP_NAME = "db_tool_app"
    USER_ID = "repo_to_paper_user"
    SESSION_ID = "session_0001"
    target_repo = "https://github.com/manubot/manubot-ai-editor"
    target_dir = str(temp_markdown_dir.resolve())
    final_output, session_state, output_events = await run_agent_workflow(
        agent=root_agent,
        prompt=f"""
            Please turn this repository and a filepath provided in the state
            into a scientific paper abstract and revise it within a loop.
            dir: {target_dir}

            repo: {target_repo}
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


@pytest.mark.parametrize(
    "notebook_path",
    [
        ("tests/reports/demonstrate.ipynb"),
    ],
)
@pytest.mark.notebooks
def test_notebook_report_generation(notebook_path: str):
    """
    Generates notebooks for reports within testing.
    """
    _ = run_notebook(
        input_path=pathlib.Path(notebook_path),
        output_path=pathlib.Path(notebook_path),
    )
    assert pathlib.Path(notebook_path).is_file()
