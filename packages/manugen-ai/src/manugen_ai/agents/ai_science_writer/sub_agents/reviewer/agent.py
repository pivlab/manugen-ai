"""
Agent for reviewing and improving written work in a loop.
"""

import os

from google.adk.agents import Agent, LoopAgent
from manugen_ai.agents.meta_agent import StopChecker
from manugen_ai.utils import get_llm

# Environment-driven model names
MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")
LLM = get_llm(MODEL_NAME)
COMPLETION_PHRASE = "TASK COMPLETED!"

agent_review_loop = Agent(
    model=LLM,
    name="review_and_decide",
    description="Critique full markdown and decide if it's finalized.",
    instruction=f"""
You receive content from the user.

Your job:
1. Provide a concise bullet-list of any changes needed.
    - Use clear, actionable language.
    - Focus on clarity, coherence, and scientific rigor.
    - If changes are needed, return a list of feedback bullets.
    - Don't go overboard, try to keep it concise and reasonable when it comes to updates.
    - Do NOT provide guidance about new topics. You are to stick to only the topic areas within the content.
2. If **no** changes are needed (content is publication-ready), response ONLY with "{COMPLETION_PHRASE}" instead of returning bullets.

Return ONLY ONE of the following.
DO NOT return both!
1. A list of feedback bullets for use with revision.
2. Or respond with ONLY "{COMPLETION_PHRASE}" to indicate the content is ready for publication
If you respond with "{COMPLETION_PHRASE}", do not include any additional text or commentary.
""",
    output_key="feedback",
)

# 2) Your existing refine agent
agent_refine = Agent(
    model=LLM,
    name="refine_manuscript",
    description="Apply feedback to revise the manuscript.",
    instruction=f"""
You receive:
- Content from the user.
- feedback: a list of bullets in {{feedback}}

Revise the content accordingly and return *only* updated content.
You MUST return actual content, not instructions or commentary about the content.
Do not add additional headers which are not in the original content.
Do not include "{COMPLETION_PHRASE}" in the output.
Do not include a header about the feedback.
Do NOT return additional commentary, JSON, or metadata.
ONLY return the revised content.
The revised content should be in markdown format and not include any additional
wrappers (such as backticks ```) or formatting besides what was provided in the original content.
""",
    output_key="refined_md",
)

# 3) Wrap them in a LoopAgent
root_agent = LoopAgent(
    name="reviewer_agent",
    description="Iteratively review and refine the manuscript until publication-ready.",
    sub_agents=[
        agent_review_loop,
        agent_refine,
        # use stopchecker to check if the work is completed.
        StopChecker(context_variable="feedback", completion_phrase=COMPLETION_PHRASE),
    ],
    max_iterations=5,  # safety cap
)
