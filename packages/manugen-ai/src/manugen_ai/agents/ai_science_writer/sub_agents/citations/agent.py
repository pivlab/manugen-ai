"""
An agent workflow to enhance content
using openalex.
"""

from __future__ import annotations

import os

from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from manugen_ai.agents.meta_agent import ResilientToolAgent
from manugen_ai.tools.tools import openalex_query, parse_list

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")
LLM = LiteLlm(model=MODEL_NAME)

parse_list_tool = FunctionTool(func=parse_list)
oa_search_tool = FunctionTool(func=openalex_query)

# Extract free-text topics
agent_extract_topics = Agent(
    model=LLM,
    name="extract_topics",
    description="Extract 3–5 key research topics from the draft; output as bullet points, one per line.",
    instruction="""
You get the user’s draft text in the user prompt.
List the 3–5 most relevant research topics as a comman-separated bullet list like this:
topic one, topic two, ...
Return only the topics, no extra commentary or JSON.
Do NOT comment on the topics or provide explanations.
""",
    output_key="topics",
)

# Search OpenAlex
agent_search_openalex = ResilientToolAgent(
    Agent(
        model=LLM,
        name="search_open_alex",
        description="Use `openalex_query` on the list `topics` to get top paper URLs.",
        instruction="""
Call `openalex_query` with `{topics}`.
Return the mapping as `search_results` (topic → list of URLs).
Do NOT provide code to perform this action - you must do it by invoking the tool calls.
""",
        tools=[oa_search_tool],
        output_key="search_results",
    ),
    max_retries=3,
)

# Improve draft
agent_improve_draft = Agent(
    model=LLM,
    name="improve_draft",
    description="Rewrite the original draft using insights from `papers`.",
    instruction="""
You get:
- Original draft: provided from the user prompt.
- Fetched papers: `{search_results}`
Incorporate relevant findings, facts, or citations into the draft.
Output only the revised draft text.
""",
    output_key="enhanced_draft",
)

# Full pipeline
root_agent = SequentialAgent(
    name="citation_agent",
    description="Extract topics → search & fetch → improve draft",
    sub_agents=[
        agent_extract_topics,
        agent_search_openalex,
        agent_improve_draft,
    ],
)
