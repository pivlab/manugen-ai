"""
Agent for revising written work in a loop.
"""


import json
import os

from google.adk.agents import Agent, LoopAgent, ParallelAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from manugen_ai.agents.meta_agent import ResilientToolAgent, SectionWriterAgent
from manugen_ai.tools.tools import exit_loop, fetch_url, json_conforms_to_schema
from manugen_ai.utils import prepare_ollama_models_for_adk_state


# Preconfigure Ollama models for ADK
prepare_ollama_models_for_adk_state()

# Environment-driven model names
GENERAL_MODEL = os.environ.get("MAI_GENERAL_MODEL_NAME", "openai/llama3.2:3b")
DRAFT_MODEL = os.environ.get("MAI_DRAFT_MODEL_NAME", GENERAL_MODEL)
REVIEW_MODEL = os.environ.get("MAI_REVIEW_MODEL_NAME", GENERAL_MODEL)
COMPLETION_PHRASE = "THE AGENT HAS COMPLETED THE TASK."

# LLM wrappers
DRAFT_LLM = LiteLlm(model=DRAFT_MODEL)
REVIEW_LLM = LiteLlm(model=REVIEW_MODEL)

agent_review_loop = Agent(
    model=REVIEW_LLM,
    name="review_and_decide",
    description="Critique full markdown and decide if it's final.",
    instruction="""
You receive:
- full_md: the full manuscript markdown in {full_md}

Your job:
1. Provide a concise bullet-list of any changes needed.
2. If **no** changes are needed (manuscript is publication-ready), call the tool `exit_loop` instead of returning bullets.

Return either:
- A JSON list of feedback bullets,
- Or invoke `exit_loop` (via the FunctionTool) to end the loop.
""",
    tools=[FunctionTool(func=exit_loop)],
    output_key="feedback",
)

# 2) Your existing refine agent
agent_refine = Agent(
    model=DRAFT_LLM,
    name="refine_manuscript",
    description="Apply feedback to revise the manuscript.",
    instruction="""
You receive:
- full_md: the current manuscript in {full_md}
- feedback: a list of bullets in {feedback}

Revise the manuscript accordingly and return updated markdown as 'refined_md'.
""",
    output_key="refined_md",
)

# 3) Wrap them in a LoopAgent
root_agent = LoopAgent(
    name="review_refine_loop",
    # Use ResilientToolAgent so missing-tool errors auto-retry up to N times
    sub_agents=[
        ResilientToolAgent(agent_review_loop, max_retries=2),
        ResilientToolAgent(agent_refine, max_retries=2),
    ],
    max_iterations=5,  # safety cap
)