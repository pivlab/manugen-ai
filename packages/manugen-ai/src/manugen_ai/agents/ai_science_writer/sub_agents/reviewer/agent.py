"""
Agent for reviewing and improving written work in a loop.
"""

import os

from google.adk.agents import Agent, LoopAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from manugen_ai.agents.meta_agent import ResilientToolAgent
from manugen_ai.tools.tools import exit_loop
from manugen_ai.utils import get_llm

# Environment-driven model names
MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")
LLM = get_llm(MODEL_NAME)
COMPLETION_PHRASE = "THE AGENT HAS COMPLETED THE TASK."

agent_review_loop = Agent(
    model=LLM,
    name="review_and_decide",
    description="Critique full markdown and decide if it's final.",
    instruction="""
You receive content from the user.

Your job:
1. Provide a concise bullet-list of any changes needed.
2. If **no** changes are needed (content is publication-ready), call the tool `exit_loop` instead of returning bullets.

Return either:
- A JSON list of feedback bullets,
- Or invoke `exit_loop` (via the FunctionTool) to end the loop.
""",
    tools=[FunctionTool(func=exit_loop)],
    output_key="feedback",
)

# 2) Your existing refine agent
agent_refine = Agent(
    model=LLM,
    name="refine_manuscript",
    description="Apply feedback to revise the manuscript.",
    instruction="""
You receive:
- Content from the user.
- feedback: a list of bullets in {feedback}

Revise the content accordingly and return *only* updated content.
Do NOT return additional commentary, JSON, or metadata.
ONLY return the revised content.
""",
    output_key="refined_md",
)

# 3) Wrap them in a LoopAgent
root_agent = LoopAgent(
    name="reviewer_agent",
    description="Iteratively review and refine the manuscript until publication-ready.",
    # Use ResilientToolAgent so missing-tool errors auto-retry up to N times
    sub_agents=[
        ResilientToolAgent(agent_review_loop, max_retries=2),
        ResilientToolAgent(agent_refine, max_retries=2),
    ],
    max_iterations=5,  # safety cap
)
