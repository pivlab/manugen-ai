"""
Agent for taking a markdown-based outline
of a scientific paper and converting it
into a content-rich and cohesive whole.
"""

from __future__ import annotations

import json
import os

from google.adk.agents import Agent, LoopAgent, ParallelAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from manugen_ai.agents.meta_agent import ResilientToolAgent, SectionWriterAgent, StopChecker
from manugen_ai.tools.tools import exit_loop, fetch_url, json_conforms_to_schema
from manugen_ai.utils import prepare_ollama_models_for_adk_state

# Preconfigure Ollama models for ADK
prepare_ollama_models_for_adk_state()

# Environment-driven model names
GENERAL_MODEL = os.environ.get("MAI_GENERAL_MODEL_NAME", "openai/command-r")
DRAFT_MODEL = os.environ.get("MAI_DRAFT_MODEL_NAME", GENERAL_MODEL)
REVIEW_MODEL = os.environ.get("MAI_REVIEW_MODEL_NAME", GENERAL_MODEL)
COMPLETION_PHRASE = "THE AGENT HAS COMPLETED THE TASK."

# LLM wrappers
DRAFT_LLM = LiteLlm(model=DRAFT_MODEL)
REVIEW_LLM = LiteLlm(model=REVIEW_MODEL)

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "sections": {"type": "array", "items": {"type": "string"}},
        "urls": {"type": "array", "items": {"type": "string", "format": "uri"}},
    },
    "required": ["title", "keywords", "sections", "urls"],
}

# Parse markdown outline
agent_parse = Agent(
    model=DRAFT_LLM,
    name="parse_outline",
    description="Parse markdown outline into title, keywords, sections, and fetch URLs.",
    instruction=f"""
Given the raw markdown outline in the user prompt extract:
- title (first H1),
- keywords list,
- ordered list of H1 sections (excluding Keywords),
- all URLs present.
Return ONLY a JSON object with keys: title, keywords, sections, urls.
Do NOT wrap the JSON within markdown, e.g. "```" or other similar syntax.
Do NOT include additional descriptive text; only include the JSON.
Do NOT include the jsonschema provided below as part of your response.

The JSON must conform to this schema:
{json.dumps(JSON_SCHEMA)}
""",
    output_key="parsed_json",
)

agent_validate = Agent(
    model=DRAFT_LLM,
    name="validate_parse",
    description="Check JSON against schema and use the completion phrase when it conforms.",
    instruction=f"""
Use the tool json_conforms_to_schema on json:
```json
{{parsed_json}}
```

with jsonschema:
```json
{json.dumps(JSON_SCHEMA)}
```

- If it returns true, the JSON conforms to the schema and you
should respond with *exactly* the phrase: "{COMPLETION_PHRASE}" (without quotations).
- Otherwise, mention that the JSON does not yet conform to the schema.

Do NOT return markdown.
""",
    tools=[FunctionTool(func=json_conforms_to_schema)],
    output_key="feedback",
)

agent_repair = Agent(
    model=DRAFT_LLM,
    name="repair_parse",
    description="Given an invalid JSON produce ONLY corrected JSON conforming to the schema.",
    instruction=f"""
This is some JSON we need to improve to match a schema below:
```json
{{parsed_json}} 
```

Here is the schema the above JSON must abide:
```json
{json.dumps(JSON_SCHEMA)}
```

Please provide ONLY the corrected JSON object (no markdown fences, no extra text) as output,
so that it fully satisfies the schema.
Do NOT provide markdown.
Do NOT provide extra commentary.
Do NOT wrap the JSON within markdown, e.g. "```" or other similar syntax.
Do NOT include additional descriptive text; only include the JSON.
Do NOT return jsonschema.
**ONLY** return improved JSON which matches the provided schema.
""",
    output_key="improved_json",
)

validate_repair_json = LoopAgent(
    name="validate_repair_json",
    sub_agents=[
        ResilientToolAgent(agent_validate, max_retries=3),
        ResilientToolAgent(agent_repair, max_retries=3),
        StopChecker(context_variable="feedback", completion_phrase=COMPLETION_PHRASE)
    ],
    max_iterations=5,
)

parse_validate_repair_json = SequentialAgent(
    name="parse_validate_repair_json", sub_agents=[agent_parse, validate_repair_json]
)

agent_fetch = Agent(
    model=DRAFT_LLM,
    name="fetch_assets",
    description="Fetch code and figure content from URLs.",
    instruction="""
You will receive a list of URLs in {parse_result[urls]}.
Your job is to:

1. Fetch each URL using tool fetch_url.
2. Store a mapping of url → content in the state.
3. Return a dictionary called 'assets' with this mapping.

Only once all URLs are successfully fetched
and the 'assets' dictionary is complete,
then call the tool exit_loop to exit the loop.
Do not call exit_loop unless all content is fetched
successfully and returned as 'assets'.
Do NOT attempt to use a tool called "fetch_assets".
""",
    tools=[FunctionTool(func=fetch_url), FunctionTool(func=exit_loop)],
    output_key="assets",
)


loop_fetch = LoopAgent(
    name="loop_fetch",
    sub_agents=[ResilientToolAgent(agent_fetch, max_retries=3)],
    max_iterations=5,
)

parallel_setup = ParallelAgent(
    name="setup",
    sub_agents=[parse_validate_repair_json, loop_fetch],
)

# Draft individual sections
agent_draft_section = Agent(
    model=DRAFT_LLM,
    name="draft_section",
    description="Draft a single paper section.",
    instruction="""
You get:
- section name: {section}
- parse info: {improved_json}
- fetched assets: {assets}
Compose the markdown for this section, embedding any relevant figure links.
""",
    output_key="section_text",
)

# instantiate the loop-writer
section_writer = SectionWriterAgent(agent_draft_section)

# Combine sections
agent_combine = Agent(
    model=DRAFT_LLM,
    name="combine_sections",
    description="Combine drafted sections into a full markdown manuscript.",
    instruction="""
You get a list `section_texts`: {section_texts}.
Merge them in the original order under their headings to produce `full_md`.
ONLY provide the markdown.
Do NOT provide additional commentary.
Do NOT wrap the markdown in "```" backticks or similar.
Do NOT return JSON data.
Do NOT provide me with code that can create markdown.
""",
    output_key="full_md",
)

# Full pipeline
root_agent = SequentialAgent(
    name="paper_pipeline",
    description="Parse outline, fetch assets, draft sections, combine, review & refine.",
    sub_agents=[
        parallel_setup,
        section_writer,
        agent_combine,
    ],
)
