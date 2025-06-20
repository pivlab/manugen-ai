import os
from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm

from manugen_ai.schema import prepare_instructions
from . import prompt

MODEL_NAME = os.environ.get(
    "MANUGENAI_FIGURE_MODEL_NAME",
    os.environ.get("MANUGENAI_MODEL_NAME"),
)

figure_agent = Agent(
    name=f"figure_agent",
    model=LiteLlm(model=MODEL_NAME),
    # include_contents="none",
    description="Agent expert in interpreting figures of a scientific article.",
    instruction=prompt.PROMPT,
    before_agent_callback=prepare_instructions,
    output_key="figure",
)