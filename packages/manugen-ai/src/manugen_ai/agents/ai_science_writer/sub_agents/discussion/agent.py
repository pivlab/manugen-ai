import os

from google.adk import Agent
from manugen_ai.schema import DISCUSSION_KEY, prepare_instructions
from manugen_ai.utils import get_llm

from . import prompt

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")
LLM = get_llm(MODEL_NAME)

discussion_agent = Agent(
    name=f"{DISCUSSION_KEY}_agent",
    model=LLM,
    include_contents="none",
    description="Agent expert in drafting or editing the Discussion section of a scientific manuscript.",
    instruction=prompt.PROMPT,
    before_agent_callback=prepare_instructions,
    output_key="discussion",
)
