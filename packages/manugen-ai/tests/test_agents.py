"""
Tests for various agents
"""

import pytest
from manugen_ai.agents.capitalizer.agent import root_agent as capitalizer_agent
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
            agent=capitalizer_agent,
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


@pytest.mark.asyncio
async def test_agent_reviewer():
    """
    Test the reviewer agent to ensure it can loop and improve text
    """

    # localized imports to help with agent env setting
    from manugen_ai.agents.ai_science_writer.sub_agents.reviewer.agent import (
        COMPLETION_PHRASE as review_agent_COMPLETION_PHRASE,
    )
    from manugen_ai.agents.ai_science_writer.sub_agents.reviewer.agent import (
        root_agent as review_agent,
    )

    # we attempt multiple times to ensure the agent can loop and improve the text
    for attempt in range(5):
        _, session_state, output_events = await run_agent_workflow(
            agent=review_agent,
            prompt="""
            Please improve the following text:

            It was a dark and stormy night.
            """,
            app_name="app",
            user_id="user",
            session_id="0001",
            # note: use `uv run pytest -s` to view the verbose stdout
            verbose=True,
        )

        # check that we received feedback and that the completion phrase was used.
        if (
            "feedback" in session_state
            and session_state["feedback"] == review_agent_COMPLETION_PHRASE
        ):
            break
        if attempt == 4:
            raise AssertionError(
                "Final attempt failed, completion phrase not found or does not match expected output."
            )
