import os

from google.adk.agents import LlmAgent
from manugen_ai.schema import METHODS_KEY, prepare_instructions
from manugen_ai.tools.tools import fetch_url
from manugen_ai.utils import get_llm

from . import prompt

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")
LLM = get_llm(MODEL_NAME)

methods_agent = LlmAgent(
    name=f"{METHODS_KEY}_agent",
    model=LLM,
    # include_contents="none",
    description="Agent expert in drafting or editing the Methods section of a scientific manuscript.",
    instruction=prompt.PROMPT,
    before_agent_callback=prepare_instructions,
    output_key="methods",
    tools=[fetch_url]
)
