"""
Tests for various agents
"""

import pytest
from manugen_ai.agents.capitalizer.agent import root_agent
from manugen_ai.utils import run_agent_workflow


@pytest.mark.asyncio
async def test_agent_capitalizer():
    APP_NAME = "app"
    USER_ID = "user"
    SESSION_ID = "001"
    expected_output = "This is a sentence to correct."

    # retry 5 times
    for attempt in range(5):
        _, session_state, _ = await run_agent_workflow(
            agent=root_agent,
            prompt="""
            this is a sentence to correct
            """,
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
            verbose=True,
        )
        if "output" in session_state and session_state["output"] == expected_output:
            break
        if attempt == 4:
            # Final attempt failed, raise assertion
            assert "output" in session_state.keys()
            assert session_state["output"] == expected_output
