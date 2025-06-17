"""
An agent workflow to enhance content
using semantic scholar (s2).
"""

from __future__ import annotations

import os

from google.adk.agents import Agent, LoopAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from manugen_ai.utils import prepare_ollama_models_for_adk_state
from manugen_ai.tools.tools import semantic_scholar_search, parse_list, fetch_url

prepare_ollama_models_for_adk_state()

TOPIC_MODEL = os.environ.get("MAI_GENERAL_MODEL_NAME", "openai/llama3.2:3b")
SEARCH_MODEL = os.environ.get("MAI_DRAFT_MODEL_NAME", TOPIC_MODEL)
IMPROVE_MODEL = os.environ.get("MAI_REVIEW_MODEL_NAME", TOPIC_MODEL)

TOPIC_LLM = LiteLlm(model=TOPIC_MODEL)
SEARCH_LLM = LiteLlm(model=SEARCH_MODEL)
IMPROVE_LLM = LiteLlm(model=IMPROVE_MODEL)

parse_list_tool = FunctionTool(func=parse_list)
s2_search_tool = FunctionTool(func=semantic_scholar_search)

# Extract free-text topics
agent_extract_topics = Agent(
    model=TOPIC_LLM,
    name="extract_topics",
    description="Extract 3–5 key research topics from the draft; output as bullet points, one per line.",
    instruction="""
You get the user’s draft text in the user prompt.
List the 3–5 most relevant research topics as bullet points:
- topic one
- topic two
- ...
Return only those lines, no extra commentary or JSON.
""",
    output_key="topics_text",
)

# Parse text topics into list
agent_parse_topics = Agent(
    model=TOPIC_LLM,
    name="parse_topics",
    description="Convert bullet-list in `{topics_text}` into a Python list of topics.",
    instruction="""
Call the tool `parse_list` on `{topics_text}` and return the resulting Python list.
Store the result in `topics`.
""",
    tools=[parse_list_tool],
    output_key="topics",
)

seq_topics = SequentialAgent(
    name="get_topics_list",
    description="Extract and structure topics list from draft",
    sub_agents=[agent_extract_topics, agent_parse_topics],
)

# Search Semantic Scholar
agent_search_scholar = Agent(
    model=SEARCH_LLM,
    name="search_semantic_scholar",
    description="Use `semantic_scholar_search` on the list `topics` to get top paper URLs.",
    instruction="""
Call `semantic_scholar_search` with `{topics}`.
Return the mapping as `search_results` (topic → list of URLs).
""",
    tools=[s2_search_tool],
    output_key="search_results",
)

# Fetch paper contents
agent_fetch_papers = Agent(
    model=SEARCH_LLM,
    name="fetch_paper_contents",
    description="Fetch each URL in `search_results` via `fetch_url` and collect text.",
    instruction="""
You get `{search_results}` mapping each topic to URLs.
For each URL, call tool `fetch_url(url)` and collect the returned text.
Return a dict `papers` mapping URL → content.
Do not try to use a tool called fetch_paper_contents.
""",
    tools=[FunctionTool(func=fetch_url)],
    output_key="papers",
)

loop_search_and_fetch = LoopAgent(
    name="gather_scholar_data",
    description="Search & fetch loop",
    sub_agents=[agent_search_scholar, agent_fetch_papers],
    max_iterations=3,
)

# Improve draft
agent_improve_draft = Agent(
    model=IMPROVE_LLM,
    name="improve_draft",
    description="Rewrite the original draft using insights from `papers`.",
    instruction="""
You get:
- Original draft: provided from the user prompt.
- Fetched papers: `{papers}`
Incorporate relevant findings, facts, or citations into the draft.
Output only the revised draft text.
""",
    output_key="enhanced_draft",
)

# Full pipeline
root_agent = SequentialAgent(
    name="s2_enhancement_pipeline",
    description="Extract topics → search & fetch → improve draft",
    sub_agents=[
        seq_topics,
        loop_search_and_fetch,
        agent_improve_draft,
    ],
)