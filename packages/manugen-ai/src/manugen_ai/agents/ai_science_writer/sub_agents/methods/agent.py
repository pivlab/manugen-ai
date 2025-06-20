import os
from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool

from manugen_ai.schema import prepare_instructions, INSTRUCTIONS_KEY, METHODS_KEY
from . import prompt

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")

methods_agent = Agent(
    name=f"{METHODS_KEY}_agent",
    model=LiteLlm(model=MODEL_NAME),
    include_contents="none",
    description="Agent expert in drafting or editing the Methods section of a scientific manuscript.",
    instruction=prompt.PROMPT,
    before_agent_callback=prepare_instructions,
    output_key="methods",
)
