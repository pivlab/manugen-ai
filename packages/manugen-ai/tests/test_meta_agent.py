"""
Tests for meta agents
"""

import os

import pytest
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from manugen_ai.agents.meta_agent import ResilientToolAgent
from manugen_ai.utils import prepare_ollama_models_for_adk_state, run_agent_workflow


@pytest.mark.asyncio
async def test_ResilientToolAgent():
    """
    Tests for ResilientToolAgent
    """

    # preconfigure ollama for use with google-adk
    prepare_ollama_models_for_adk_state()

    # LLM wrappers
    DRAFT_LLM = LiteLlm(
        model=os.environ.get("MAI_GENERAL_MODEL_NAME", "openai/llama3.2:3b")
    )

    def example_tool():
        """
        An example function which takes no arguments
        and returns nothing.
        """
        pass

    root_agent = ResilientToolAgent(
        wrapped_agent=Agent(
            model=DRAFT_LLM,
            name="agent1",
            description=("Example"),
            instruction="""
    Use example_too to perform an example
    run of a tool in google-adk.
    """,
            tools=[example_tool],
            output_key="example",
        ),
        max_retries=5,
    )

    APP_NAME = "app"
    USER_ID = "user"
    SESSION_ID = "0001"
    final_output, session_state, output_events = await run_agent_workflow(
        agent=root_agent,
        prompt="""
        Use the agent instructions to determine what to do.
        """,
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        # note: use `uv run pytest -s` to view the verbose stdout
        verbose=True,
    )

    assert "example" in session_state.keys()
