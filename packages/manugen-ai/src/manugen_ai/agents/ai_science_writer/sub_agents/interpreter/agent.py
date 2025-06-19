import os
import json
from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

from manugen_ai.schema import ManuscriptStructure
from . import prompt

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")

request_interpreter_agent = Agent(
    name="request_interpreter_agent",
    model=LiteLlm(model=MODEL_NAME),
    # include_contents="none",
    description="It interprets the user's input/request, extracts subrequests/ideas from it and assign them to specific sections of the scientific manuscript.",
    instruction=prompt.PROMPT,
    output_schema=ManuscriptStructure,
    output_key="instructions"
)
# async def call_request_interpreter_agent(
#     question: str,
#     tool_context: ToolContext,
# ):
#     """Tool to call the request_interpreter_agent."""
#     agent_tool = AgentTool(
#         agent=request_interpreter_agent,
#         # skip_summarization=True,
#     )
# 
#     agent_output = await agent_tool.run_async(
#         args={"request": question},
#         tool_context=tool_context
#     )
#     tool_context.state[INSTRUCTIONS_KEY] = agent_output
#     return agent_output