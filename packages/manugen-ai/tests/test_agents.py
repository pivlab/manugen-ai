"""
Tests for various agents
"""

from manugen_ai.agents.capitalizer.agent import root_agent
from manugen_ai.utils import run_agent_workflow
import pytest


@pytest.mark.asyncio
async def test_agent_capitalizer():
    APP_NAME = "app"
    USER_ID = "user"
    SESSION_ID = "001"
    _, session_state, _ = await run_agent_workflow(
        agent=root_agent,
        prompt="""
        this is a sentence to correct
        """,
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        # note: use `uv run pytest -s` to view the verbose stdout
        verbose=True,
    )
    # assert we have an abstract which was added
    assert "output" in session_state.keys()
    assert session_state["output"] == "This is a sentence to correct."
