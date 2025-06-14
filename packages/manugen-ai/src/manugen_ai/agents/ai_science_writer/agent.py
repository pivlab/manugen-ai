import os
import json
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import Optional

model_api_base = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")

# when using the openai provider we need a /v1 suffix, so if it doesn't end in /v1, add it
if not model_api_base.endswith("/v1"):
    model_api_base += "/v1"

os.environ["OPENAI_API_BASE"] = model_api_base
os.environ["OPENAI_API_KEY"] = "unused"

MODEL_NAME = "openai/qwen3:30b"

introduction_agent = Agent(
    name="introduction_agent",
    model=LiteLlm(model=MODEL_NAME),
    include_contents='none',
    description="Handles the drafting of the Introduction section of a scientific manuscript.",
    instruction="""
    You are an expert in drafting the Introduction section of a scientific manuscript.
    Take the rough structure of the manuscript provided by the user (either in Markdown or LaTeX), extract the instructions
    provided under the Introduction section, and draft a properly structured Introduction section.
    """.strip(),
)
# introduction_writer = AgentTool(agent=introduction_agent, skip_summarization=True)

results_agent = Agent(
    name="results_agent",
    model=LiteLlm(model=MODEL_NAME),
    include_contents='none',
    description="Handles the drafting of the Results section of a scientific manuscript.",
    instruction="You are an expert in drafting the Results section of a scientific manuscript. "
                "Take the rough structure of the manuscript provided by the user (either in Markdown or LaTeX), extract the instructions "
                "provided under the Results section, and draft a properly structured "
                "Results section.",
)
# results_writer = AgentTool(agent=results_agent, skip_summarization=True)

# ccc_agent = Agent(
#     name="ccc_agent",
#     model=LiteLlm(model=MODEL_NAME),
#     description="Handles requests to check whether input text follows the context-content-conclusion (C-C-C) scheme."
# )

from pydantic import BaseModel, Field

class UserInstructions(BaseModel):
    introduction: str = Field(description="Introduction instructions.")
    results: str = Field(description="Results instructions.")

article_structure_agent = Agent(
    name="article_structure_agent",
    model=LiteLlm(model=MODEL_NAME),
    description="Extracts sections of the user input.",
    instruction=f"""
    Given the input in Markdown format, extract the Introduction and Results, including all their content.
    Respond ONLY with a JSON object matching this exact schema:
    {json.dumps(UserInstructions.model_json_schema(), indent=2)}
    """.strip(),
    output_schema=UserInstructions,
    output_key="instructions"
)

def prepare_results_input(callback_context: CallbackContext) -> Optional[types.Content]:
    current_state = callback_context.state.to_dict()
    callback_context.state["results_instructions"] = current_state["instructions"]["results"]
    return None

results_output_agent = Agent(
    name="results_output_agent",
    model=LiteLlm(model=MODEL_NAME),
    include_contents="none",
    description="Extracts sections of the user input.",
    instruction="""
    Given the rough instructions to write a Results section below, draft a proper Results
    section for a scientific article.
    
    **Instructions for Results section**:
    ```
    {results_instructions}
    ```
    
    **Output:**
    Output only the fully structured Results section.
    """.strip(),
    before_agent_callback=prepare_results_input,
)

root_agent = SequentialAgent(
    name="scientific_article_writer",
    description="Writes a scientific article",
    sub_agents=[
        article_structure_agent,
        results_output_agent,
        # results_agent,
        # introduction_extractor_agent,
        # introduction_agent,
    ],
)

# root_agent = Agent(
#     name="ai_science_writer",
#     model=LiteLlm(model=MODEL_NAME),
#     description="The main coordinator agent to draft a scientific manuscript given the user's instructions.",
#     instruction="""
#     You are the main scientific writer coordinating a team. Your primary responsibility is to help draft a scientific article.
#     The user's input should be the basic structure of a scientific manuscript (either in Markdown or LaTeX).
#     This structure might have some common sections in any scientific article, such as the Title, Abstract,
#     Introduction, Results, Discussion and/or Methods.
#     Under each section, the user will provide some very rough instructions or ideas on how to draft it.
#     Your goal is to draft the scientific article including only the sections specified by the user.
#     You'll follow these steps:
#     1. You first have to draft the Results section. For this, you first need to extract the specific instructions for the Results section by delegating to the "results_extractor_agent"
#     """.strip(),
#     # tools=[results_writer, introduction_writer], # Root agent still needs the weather tool for its core task
#     # Key change: Link the sub-agents here!
#     sub_agents=[results_agent, introduction_agent]
# )


# root_agent = Agent(
#     name="ai_science_writer",
#     model=LiteLlm(model=MODEL_NAME),
#     description="The main coordinator agent to draft a scientific manuscript given the user's instructions.",
#     instruction="You are the main Science Writer coordinating a team. Your primary responsibility is to help draft a scientific article. "
#                 "You have two specialized agents: "
#                 "1. 'results_agent': Drafts the Results section given the specific instructions for this section. Delegate to this agent to draft the Results section. "
#                 "2. 'introduction_agent': Drafts the Introduction section given the specific instructions for this section. Delegate to this agent to draft the Introduction section. "
#                 "Analyze the user's input, which should be the basic structure of a scientific manuscript (either in Markdown or LaTeX). "
#                 "This structure will have some common sections in any scientific article, such as the Title, Abstract, "
#                 "Introduction, Results, Discussion or Methods. "
#                 "Under each section, the user will provide some very rough instructions on how to draft it. "
#                 "Your goal is to draft the entire scientific article by following the user's instructions. "
#                 "You first need to draft the Results section. "
#                 "Then, you need to continue with the Introduction section. "
#                 "Return the draft of the scientific manuscript in the same format of the input (either Markdown or LaTeX). "
#                 "Include only the sections that are mentioned in the user's input and those for which you have specialized agents to draft them. "
#                 "Ignore any other section in your output.",
#     # tools=[results_writer, introduction_writer], # Root agent still needs the weather tool for its core task
#     # Key change: Link the sub-agents here!
#     sub_agents=[results_agent, introduction_agent]
# )