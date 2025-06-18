"""
Tests for meta agents
"""

import os

import pytest
from google.adk.agents import Agent, LoopAgent
from google.adk.models.lite_llm import LiteLlm
from manugen_ai.agents.meta_agent import ResilientToolAgent, StopChecker
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


@pytest.mark.asyncio
async def test_StopChecker():
    """
    Tests for StopChecker
    """

    # preconfigure ollama for use with google-adk
    prepare_ollama_models_for_adk_state()

    # LLM wrappers
    DRAFT_LLM = LiteLlm(
        model=os.environ.get("MAI_GENERAL_MODEL_NAME", "openai/llama3.2:3b")
    )

    COMPLETION_PHRASE = "THIS IS FINE!"

    MAX_LOOPS = 8

    reviewer_agent = Agent(
            model=DRAFT_LLM,
            name="reviewer",
            description=("You are an reviewer."),
            instruction=f"""
            Identify whether the story length needs to be increased.
            Your *only* guideline is that the story must be 2 or more sentences long
            Focus on making feedback concise and quick - we don't want too much revision!
            Provide these specific suggestions concisely. Output *only* the critique text.

            ELSE IF there is no feedback and the document is good:
            Respond *exactly* with the phrase: "{COMPLETION_PHRASE}" and nothing else (excluding quotes). 
            It doesn't need to be perfect, just functionally complete for this stage.
            Avoid suggesting purely subjective stylistic preferences if the core is sound.
            """,
            output_key="feedback",
        )
    
    writer_agent = Agent(
            model=DRAFT_LLM,
            name="writer",
            description=("You are a writer."),
            instruction=f"""
            Take feedback from a reviewer and improve the content.

            The feedback is avaialable here:
            ```    
            {{feedback}}
            ```

            If the feedback is equal to {COMPLETION_PHRASE} please
            simply provide **ONLY** the content with no additional commentary.
            """,
            output_key="content",
        )
    
    # loop for refining the initial content
    root_agent = LoopAgent(
        name="refiner",
        sub_agents=[reviewer_agent, writer_agent, StopChecker(context_variable="feedback", completion_phrase=COMPLETION_PHRASE)],
        max_iterations=MAX_LOOPS,
    )
    

    APP_NAME = "app"
    USER_ID = "user"
    SESSION_ID = "0001"
    final_output, session_state, output_events = await run_agent_workflow(
        agent=root_agent,
        prompt="""
        Please improve the following text:

        It was a dark and stormy night.
        """,
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        # note: use `uv run pytest -s` to view the verbose stdout
        verbose=True,
    )

    print(output_events)
    editor_count = sum(1 for ev in output_events if ev.get("agent") == "writer")
    print(f"The editor agent ran {editor_count} times")

    assert "feedback" in session_state.keys()
    # test that we exited the loop earlier than the max number of loops
    assert editor_count < MAX_LOOPS
