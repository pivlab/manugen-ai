import os

from google.adk import Agent
from manugen_ai.schema import INTRODUCTION_KEY, prepare_instructions
from manugen_ai.utils import get_llm

from . import prompt

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")
LLM = get_llm(MODEL_NAME)

introduction_agent = Agent(
    name=f"{INTRODUCTION_KEY}_agent",
    model=LLM,
    include_contents="none",
    description="Agent expert in drafting or editing an Introduction section of a scientific manuscript.",
    instruction=prompt.PROMPT,
    before_agent_callback=prepare_instructions,
    output_key="introduction",
)
