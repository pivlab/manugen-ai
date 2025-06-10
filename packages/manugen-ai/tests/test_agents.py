"""
Tests for various agents
"""

from manugen_ai.agents.repo_to_paper.agent import root_agent
from manugen_ai.utils import run_agent_workflow
import pytest


@pytest.mark.asyncio
async def test_something():
    APP_NAME = "db_tool_app"
    USER_ID = "repo_to_paper_user"
    SESSION_ID = "session_0001"
    final_output, session_state, output_events = await run_agent_workflow(
        agent=root_agent,
        prompt="""
        Here's url for the repository you will turn into an abstract:
        https://github.com/manubot/manubot-ai-editor
        """,
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        initial_state={"current_document": "stub text"},
        # note: use `uv run pytest -s` to view the verbose stdout
        verbose=True,
    )
    # assert we have an abstract which was added
    assert "abstract" in session_state.keys()
