import os
from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

from manugen_ai.utils import prepare_instructions, INSTRUCTIONS_KEY, INTRODUCTION_KEY
from . import prompt

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")

introduction_agent = Agent(
    name="introduction_agent",
    model=LiteLlm(model=MODEL_NAME),
    include_contents="none",
    description="Agent expert in drafting or editing an Introduction section of a scientific manuscript.",
    instruction=prompt.PROMPT,
    before_agent_callback=prepare_instructions,
    output_key="introduction",
)


async def call_introduction_agent(
        question: str,
        tool_context: ToolContext,
):
    """Tool to call the introduction_agent."""
    section_key = INTRODUCTION_KEY
    agent_obj = introduction_agent

    agent_tool = AgentTool(
        agent=agent_obj,
        # skip_summarization=True,
    )

    agent_output = await agent_tool.run_async(
        # args={"request": question},
        args={"request": "Follow your original instructions."},
        tool_context=tool_context,
    )
    # save results
    tool_context.state[section_key] = agent_output

    # remove current instructions since we already applied them
    if section_key in tool_context.state[INSTRUCTIONS_KEY]:
        del tool_context.state[INSTRUCTIONS_KEY][section_key]
    tool_context.state[f"{INSTRUCTIONS_KEY}_{section_key}"] = ""

    return agent_output