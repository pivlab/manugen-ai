import os

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from ..manuscript_drafter import manuscript_drafter_agent
from . import prompt

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")

coordinator_agent = LlmAgent(
    name="coordinator_agent",
    model=LiteLlm(model=MODEL_NAME),
    description="Coordinator agent for scientific manuscript writing.",
    instruction=prompt.PROMPT,
    sub_agents=[
        manuscript_drafter_agent,
        # reviewer_agent,
        # citation_agent,
        # figure_agent,
        # python_agent,
    ]
)
