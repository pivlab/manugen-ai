from __future__ import annotations
import os

from google.adk.agents import Agent, LoopAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from manugen_ai.agents.meta_agent import ResilientToolAgent
from manugen_ai.tools.tools import parse_list, openalex_query
from manugen_ai.data import search_withdrarxiv_embeddings
from manugen_ai.utils import prepare_ollama_models_for_adk_state

# Initialize Ollama/OpenAI models
prepare_ollama_models_for_adk_state()
TOPIC_MODEL = os.environ.get("MAI_GENERAL_MODEL_NAME", "openai/llama3.2")
SEARCH_MODEL = os.environ.get("MAI_DRAFT_MODEL_NAME", TOPIC_MODEL)
IMPROVE_MODEL = os.environ.get("MAI_REVIEW_MODEL_NAME", TOPIC_MODEL)

TOPIC_LLM = LiteLlm(model=TOPIC_MODEL)
SEARCH_LLM = LiteLlm(model=SEARCH_MODEL)
IMPROVE_LLM = LiteLlm(model=IMPROVE_MODEL)

# Tools
parse_list_tool = FunctionTool(func=parse_list)
openalex_tool   = FunctionTool(func=openalex_query)

# RAG-specific embedding & retraction tool
embeddings_function = FunctionTool(
    func=search_withdrarxiv_embeddings,
)

# Synthesize a concise abstract for embedding queries
agent_synthesize_abstract = Agent(
    model=TOPIC_LLM,
    name="synthesize_abstract",
    description="Generate a concise abstract from the draft for embedding retrieval.",
    instruction="""
Take the user’s full draft and synthesize a concise abstract summarizing key contributions
and context. Output only the abstract text.
""",
    output_key="synthesized_abstract",
)

# Retrieve retraction notices via embeddings
agent_fetch_retractions = ResilientToolAgent(
    Agent(
        model=SEARCH_LLM,
        name="fetch_retractions",
        description=(
            "Use `search_withdrarxiv_embeddings` on the synthesized abstract to get related retraction notices."
        ),
        instruction="""
Call `search_withdrarxiv_embeddings` with `{synthesized_abstract}`.
Return the mapping as `retraction_notices` (e.g., arXiv ID → retraction reason/details).
""",
        tools=[embeddings_function],
        output_key="retraction_notices",
    ),
    max_retries=3,
)

# Improve draft using retrieved retraction insights
agent_improve_draft = Agent(
    model=IMPROVE_LLM,
    name="improve_draft",
    description="Rewrite the original draft using insights from `retraction_notices`.",
    instruction="""
You get:
- Original draft: provided from the user prompt.
- Related retraction notices: `{retraction_notices}`
Incorporate lessons, caveats, and citations into the draft to improve its rigor.
Do NOT mention retractions notices directly.
Output **only** the enhanced draft text without additional commentary.
""",
    output_key="enhanced_draft",
)

agent_finalize_improvements = Agent(
    model=IMPROVE_LLM,
    name="agent_finalize_improvements",
    description="Finalize the improvements provided from `enhanced_draft`.",
    instruction="""
You get a revised draft:
```
{enhanced_draft}
```
Please return *only* the enhanced_draft text without 
additional commentary or markdown formatting.
Clean it up so that we only have the draft content in a similar format to what
was provided in the user prompt.
Do NOT include wrappings or fences like "```" or other similar syntax.
If you find that there are fences like "```" or other similar syntax near the beginning
or the end of the draft,
please remove them from the output.
""",
    output_key="finalized_draft",
)

# 5. Loop: synthesize + fetch up to 3 iterations
rag_loop = LoopAgent(
    name="rag_retrieval_loop",
    description="Loop to synthesize abstract and retrieve retractions",
    sub_agents=[agent_synthesize_abstract, agent_fetch_retractions, agent_improve_draft],
    max_iterations=2,
)

root_agent = SequentialAgent(
    name="rag_retrieval_pipeline",
    description="Finalize the improved draft from `enhanced_draft`",
    sub_agents=[rag_loop, agent_finalize_improvements]
    )


