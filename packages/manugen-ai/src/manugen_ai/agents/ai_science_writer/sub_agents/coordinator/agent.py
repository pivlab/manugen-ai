import os

from google.adk.agents import LlmAgent
from manugen_ai.utils import get_llm

from ..citations import root_agent as citation_agent
from ..figure import figure_agent
from ..manuscript_drafter import manuscript_drafter_agent
from ..repo_to_paper import root_agent as repo_agent
from ..retraction_avoidance import root_agent as retraction_avoidance_agent
from ..reviewer import root_agent as review_agent
from . import prompt

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")
LLM = get_llm(MODEL_NAME)

coordinator_agent = LlmAgent(
    name="coordinator_agent",
    model=LLM,
    description="Coordinator agent for scientific manuscript writing.",
    instruction=prompt.PROMPT,
    sub_agents=[
        manuscript_drafter_agent,
        figure_agent,
        retraction_avoidance_agent,
        citation_agent,
        review_agent,
        repo_agent,
    ],
)
