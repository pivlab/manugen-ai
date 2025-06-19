import os
import json
from pathlib import Path
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import Optional

from .sub_agents.introduction import call_introduction_agent
from .sub_agents.results import call_results_agent
from .sub_agents.title import call_title_agent
from .sub_agents.abstract import call_abstract_agent
from .sub_agents.discussion import call_discussion_agent
from .sub_agents.methods import call_methods_agent
from .sub_agents.drafter import drafter_agent

from manugen_ai.utils import ManuscriptStructure, prepare_instructions, INSTRUCTIONS_KEY, TITLE_KEY, ABSTRACT_KEY, INTRODUCTION_KEY, DISCUSSION_KEY, METHODS_KEY

# MODEL_NAME = "ollama/qwen3:30b"
# MODEL_NAME = "ollama/qwen3:30b-a3b"
# MODEL_NAME = "ollama/qwen3:32b"
# MODEL_NAME = "anthropic/claude-3-7-sonnet-20250219"
# MODEL_NAME = "openai/gpt-4o-mini"
# MODEL_NAME = "openai/o4-mini"
MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")
os.environ["OPENAI_API_BASE"] = ""

# when using the openai provider we need a /v1 suffix, so if it doesn't end in /v1, add it
# model_api_base = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
# if MODEL_NAME.startswith(("ollama",)):
#     MODEL_NAME.replace("ollama", "openai")
#     if not model_api_base.endswith("/v1"):
#         model_api_base += "/v1"
# 
#     os.environ["OPENAI_API_BASE"] = model_api_base
#     os.environ["OPENAI_API_KEY"] = "unused"

# MANUSCRIPT_DIR = Path("/home/miltondp/projects/pivlab/adk-hackathon-2025/adk-hack-2025/packages/manugen-ai/src/manugen_ai/agents/ai_science_writer/rootstock/content").resolve()
# assert MANUSCRIPT_DIR.exists()

# ccc_agent = Agent(
#     name="ccc_agent",
#     model=LiteLlm(model=MODEL_NAME),
#     description="Handles requests to check whether input text follows the context-content-conclusion (C-C-C) scheme."
# )






# async def call_manuscript_section_agent(
#         question: str,
#         tool_context: ToolContext,
#         section_key: str,
#         agent_obj: Agent,
# ):
#     """Tool to call an agent."""
#     
#     section_key = SOMETHING
#     agent_obj = SOMETHING
#     
#     agent_tool = AgentTool(
#         agent=agent_obj,
#         # skip_summarization=True,
#     )
# 
#     agent_output = await agent_tool.run_async(
#         # args={"request": question},
#         args={"request": "Follow your original instructions."},
#         tool_context=tool_context,
#     )
#     # save results
#     tool_context.state[section_key] = agent_output
# 
#     # remove current instructions since we already applied them
#     del tool_context.state[INSTRUCTIONS_KEY][section_key]
#     tool_context.state[f"{INSTRUCTIONS_KEY}_{section_key}"] = ""
# 
#     return agent_output

request_interpreter_agent = Agent(
    name="request_interpreter_agent",
    model=LiteLlm(model=MODEL_NAME),
    # include_contents="none",
    description="It interprets the user's input/request, extracts subrequests/ideas from it and assign them to specific sections of the scientific manuscript.",
    instruction=f"""
    Your goal is to interpret the user's input and extract subrequests or ideas that are specific
    to different sections of the scientific manuscript. For example, the user's request might
    have subrequests/ideas that are specific to the Introduction or Results sections, while other
    subrequests might be broader and impact different sections such as the Title, Introduction
    and Discussion.
    
    Follow this workflow:
    1. Analyze the user's input. Identify requests, ideas (both concrete or broad), broad
    or narrow research topics, a rough set of instructions, a concrete description of an
    experiment performed, or even an earlier draft of a manuscript section in either Markdown
    or LaTeX, among other types of requests/ideas. Do not make things up, stick to what the
    user has specified. And preserve the user's input format (such as plain text, Markdown or
    LaTeX).
    2. Assign these request/ideas to specific sections of the manuscript (such as title,
    abstract, introduction, results, etc). Keep in mind that one specific request or idea could 
    be assigned to multiple sections of the manuscript. If there are no subrequests/ideas
    specific to one section, then assign an empty value for that section.
    3. Respond ONLY with a JSON object matching this schema:
    {json.dumps(ManuscriptStructure.model_json_schema(), indent=2)}
    """.strip(),
    output_schema=ManuscriptStructure,
    output_key="instructions"
)
# async def call_request_interpreter_agent(
#     question: str,
#     tool_context: ToolContext,
# ):
#     """Tool to call the request_interpreter_agent."""
#     agent_tool = AgentTool(
#         agent=request_interpreter_agent,
#         # skip_summarization=True,
#     )
# 
#     agent_output = await agent_tool.run_async(
#         args={"request": question},
#         tool_context=tool_context
#     )
#     tool_context.state[INSTRUCTIONS_KEY] = agent_output
#     return agent_output














manuscript_assembler_agent = Agent(
    name="manuscript_assembler_agent",
    model=LiteLlm(model=MODEL_NAME),
    include_contents="none",
    description="Agent that assembles all sections of the scientific manuscript to generate the final manuscript.",
    instruction="""
    You are an expert in assembling the final draft of a scientific manuscript by combining all
    the sections (provided as your input below) that were drafted by others.
    Make sure the final manuscript (your output) is in valid Markdown or LaTeX, which will depend on how
    the sections of the manuscript were drafted.
    
    # Your input (sections already drafted)
    ```
    ## Introduction
    {introduction}
    
    ## Results
    {results}
    ```

    # Your output
    Output only the content of the entire manuscript. Do not provide any explanation.
    """.strip(),
    # before_agent_callback=prepare_instructions,
)
async def call_manuscript_assembler_agent(
    question: str = "",
    tool_context: ToolContext = None,
):
    """Tool to call the manuscript_assembler_agent."""
    # agent_tool = AgentTool(
    #     agent=manuscript_assembler_agent,
    #     # skip_summarization=True,
    # )

    # agent_output = await agent_tool.run_async(
    #     # args={"request": question},
    #     args={"request": "Follow your original instructions."},
    #     tool_context=tool_context,
    # )
    # tool_context.state["introduction"] = agent_output
    return tool_context.state.get("manuscript")


# manuscript_builder_coordinator_agent = Agent(
#     name="manuscript_builder_coordinator_agent",
#     model=LiteLlm(model=MODEL_NAME),
#     description="Agent expert in coordinating a scientific manuscript writing team to "
#                 "draft from scratch or edit a scientific manuscript given instructions "
#                 "from the user.",
#     instruction=f"""
#     You are an expert in coordinating a team to write a scientific manuscript that is composed
#     of different sections such as Title, Abstract, Introduction, Results, Discussion,
#     Methods, etc.
#     Your ONLY goal is to coordinate a team of agents/tools with specific skills to draft or edit a scientific
#     manuscript.
#     This is your team of agents/tools:
#     * 'request_interpreter_agent': it help you interpret the user's input and extract
#     from it the user's subrequests/ideas that are specific to each section of the manuscript.
#     Some user's requests/ideas might not be specific to one section but instead impact
#     different sections of the manuscript such as the Title, Abstract and Introduction.
#     Always forward to this agent/tool the user's message exactly as you received it (which
#     can be plain text, Markdown or LaTeX). This agent will return a JSON object with the
#     manuscript's sections as keys and the subrequests/ideas for each section as values.
#     If the value for a key/section is not empty, it means that the user has a requested changes for
#     that section, and you should call a specialized agent to draft that section.
#     * 'title_agent': it helps you draft or edit the Title of the
#     manuscript. You should always call this agent if the user has
#     requested changes that impact this section.
#     * 'abstract_agent': it helps you draft or edit the Abstract of the
#     manuscript. You should always call this agent if the user has
#     requested changes that impact this section.
#     * 'introduction_agent': it helps you draft or edit the Introduction section of the
#     manuscript. You should always call this agent if the user has
#     requested changes that impact this section.
#     * 'results_agent': it helps you draft or edit the Results section of the
#     manuscript. You should always call this agent if the user has
#     requested changes that impact this section.
#     * 'discussion_agent': it helps you draft or edit the Discussion section of the
#     manuscript. You should always call this agent if the user has
#     requested changes that impact this section.
#     * 'methods_agent': it helps you draft or edit the Methods section of the
#     manuscript. You should always call this agent if the user has
#     requested changes that impact this section.
#     * `manuscript_assembler_agent`: it helps you assemble the final manuscript with all its
#     sections after they have been drafted/edited by other agents.
#     
#     Follow this workflow:
#     1. If the user's input IS NOT related to drafting/editing a scientific manuscript, then
#     simply disregard the request politely, state what's your goal and quit. Otherwise,
#     continue.
#     2. Interpret what the user's requesting from the latest user messages. If more context
#     is lacking, try to improve the user's request by adding more context (such as which sections
#     of the manuscript might be affected by the requests).
#     3. Call the 'request_interpreter_agent' by providing what the user wants for the
#     manuscript. This agent will return a JSON object with manuscript section names
#     as keys and requests/ideas for that section as values.
#     4. Analyze this JSON object. If the value for a section is not
#     empty, it means that there are requests for that section that need to be completed, so
#     you have to call the section-specific agent to draft it (next step). If none of the sections have
#     requests, then your response is to ask the user for more specific requests/edits and quit.
#     Otherwise, continue.
#     5. For each section that has requests, call the section-specific agent that you have
#     available to draft it, such as 'introduction_agent', 'results_agent', etc. NEVER draft/edit
#     yourself, you rely on your agents/tools to write any part of the manuscript.
#     6. Once all sections (for which you have agents for) are drafted/edited,
#     you have to call the 'manuscript_assembler_agent' at the end and ALWAYS show the returned value
#     (a full manuscript draft) to the user. Please DO NOT EDIT/CHANGE
#     IN ANY WAY this manuscript draft, just show it to the user.
#     """.strip(),
#     tools=[
#         call_request_interpreter_agent,
#         call_title_agent,
#         # call_keywords_agent,
#         call_abstract_agent,
#         call_introduction_agent,
#         call_results_agent,
#         call_discussion_agent,
#         call_methods_agent,
#         call_manuscript_assembler_agent,
#     ],
# )


wf_manuscript_builder_coordinator_agent = SequentialAgent(
    name="wf_manuscript_builder_coordinator_agent",
    description="Interpret user's input, drafts manuscript, and shows it",
    sub_agents=[
        request_interpreter_agent,
        drafter_agent,
        manuscript_assembler_agent,
    ]
)

root_agent = wf_manuscript_builder_coordinator_agent
