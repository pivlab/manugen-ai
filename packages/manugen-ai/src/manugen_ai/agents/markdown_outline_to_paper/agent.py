from __future__ import annotations

import os
import requests
from typing import AsyncGenerator

from pydantic import PrivateAttr
import json

from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.tools import FunctionTool
from google.adk.models.lite_llm import LiteLlm

from manugen_ai.utils import prepare_ollama_models_for_adk_state

# Preconfigure Ollama models for ADK
prepare_ollama_models_for_adk_state()

# Environment-driven model names
GENERAL_MODEL = os.environ.get("MAI_GENERAL_MODEL_NAME", "openai/llama3.2:3b")
DRAFT_MODEL   = os.environ.get("MAI_DRAFT_MODEL_NAME", GENERAL_MODEL)
REVIEW_MODEL  = os.environ.get("MAI_REVIEW_MODEL_NAME", GENERAL_MODEL)

# LLM wrappers
DRAFT_LLM = LiteLlm(model=DRAFT_MODEL)
REVIEW_LLM = LiteLlm(model=REVIEW_MODEL)

# --- Tools as function wrappers ---

def fetch_url(url: str) -> str:
    res = requests.get(url)
    res.raise_for_status()
    return res.text

fetch_tool = FunctionTool(func=fetch_url)

# --- Agents ---

# 1. Parse markdown outline
agent_parse = Agent(
    model=DRAFT_LLM,
    name="parse_outline",
    description="Parse markdown outline into title, keywords, sections, and fetch URLs.",
    instruction="""
Given the raw markdown outline in the user prompt extract:
- title (first H1),
- keywords list,
- ordered list of H1 sections (excluding Keywords),
- all URLs present.
Return a JSON object with keys: title, keywords, sections, urls.
""",
    output_key="parse_result",
)

# 2. Fetch assets
agent_fetch = Agent(
    model=DRAFT_LLM,
    name="fetch_assets",
    description="Fetch code and figure content from URLs.",
    instruction="""
You will receive a list of URLs in {parse_result[urls]}.
Fetch each URL and store mapping url->content in state.
Return a map 'assets'.
""",
    tools=[fetch_tool],
    output_key="assets",
)

parallel_setup = ParallelAgent(
    name="setup",
    sub_agents=[agent_parse, agent_fetch],
)

# 3. Draft individual sections
agent_draft_section = Agent(
    model=DRAFT_LLM,
    name="draft_section",
    description="Draft a single paper section.",
    instruction="""
You get:
- section name: {section}
- parse info: {parse_result}
- fetched assets: {assets}
Compose the markdown for this section, embedding any relevant figure links.
""",
    output_key="section_text",
)

# 4. Custom SectionWriterAgent
class SectionWriterAgent(BaseAgent):
    """
    Loops through parse_result['sections'], sets session.state['section'],
    invokes the draft_section agent, and accumulates outputs.
    """
    # Use a private attribute for the wrapped draft agent
    _draft_agent: Agent = PrivateAttr()

    def __init__(self, draft_agent: Agent):
        super().__init__(name="write_sections")
        # Store the draft agent privately (not a pydantic field)
        self._draft_agent = draft_agent

    async def _run_async_impl(
        self,
        ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        # Get list of sections
        print(ctx.session.state.get("parse_result", {}))
        sections = json.loads(ctx.session.state.get("parse_result", {})).get("sections", [])

        all_texts: list[str] = []
        for section in sections:
            # inject current section
            ctx.session.state["section"] = section

            # run the draft agent
            async for event in self._draft_agent._run_async_impl(ctx):
                yield event

            # collect its output
            all_texts.append(ctx.session.state.get("section_text"))

        # store all section_texts
        ctx.session.state["section_texts"] = all_texts

# instantiate the loop-writer
section_writer = SectionWriterAgent(agent_draft_section)

# 5. Combine sections
agent_combine = Agent(
    model=DRAFT_LLM,
    name="combine_sections",
    description="Combine drafted sections into a full markdown manuscript.",
    instruction="""
You get a list `section_texts`: {section_texts}.
Merge them in the original order under their H1 headings to produce `full_md`.
""",
    output_key="full_md",
)

# 6. Review & refine
agent_review = Agent(
    model=REVIEW_LLM,
    name="review_manuscript",
    description="Critique full manuscript markdown.",
    instruction="""
You get full_md in {full_md}. Provide concise feedback bullet list.
""",
    output_key="feedback",
)

agent_refine = Agent(
    model=DRAFT_LLM,
    name="refine_manuscript",
    description="Revise manuscript based on feedback.",
    instruction="""
You get:
- full_md: {full_md}
- feedback: {feedback}
Revise markdown accordingly and return 'refined_md'.
""",
    output_key="refined_md",
)

sequence_review = SequentialAgent(
    name="review_sequence",
    sub_agents=[agent_review, agent_refine],
)

# 7. Full pipeline
root_agent = SequentialAgent(
    name="paper_pipeline",
    description="Parse outline, fetch assets, draft sections, combine, review & refine.",
    sub_agents=[
        parallel_setup,
        section_writer,
        agent_combine,
        sequence_review,
    ],
)
