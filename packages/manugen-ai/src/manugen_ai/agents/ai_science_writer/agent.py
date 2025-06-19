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
    # output_key="instructions"
)
async def call_request_interpreter_agent(
    question: str,
    tool_context: ToolContext,
):
    """Tool to call the request_interpreter_agent."""
    agent_tool = AgentTool(
        agent=request_interpreter_agent,
        # skip_summarization=True,
    )

    agent_output = await agent_tool.run_async(
        args={"request": question},
        tool_context=tool_context
    )
    tool_context.state[INSTRUCTIONS_KEY] = agent_output
    return agent_output


abstract_agent = Agent(
    name="abstract_agent",
    model=LiteLlm(model=MODEL_NAME),
    include_contents="none",
    description="Agent expert in drafting or editing the Abstract of a scientific manuscript.",
    instruction="""
    You are an expert in drafting or editing the Abstract of a scientific manuscript.
    Your goal is to either:
    1) Draft the Abstract from scratch: if there is no current draft of the Abstract,
    you will draft an Abstract from scratch using the user's instructions below and any
    other relevant section of the manuscript;
    2) Edit an existing Abstract: if there is a current draft of the Abstract,
    you will edit it using the user's instructions below and any
    other relevant section of the manuscript;

    Below you'll find the current draft of the Abstract (if present), a rough set of
    instructions from the user on how to draft it from scratch or edit an existing Abstract,
    the guidelines that you have to follow to correctly structure the Abstract,
    and any other parts of the manuscript that might be relevant for you (such as the current
    draft of the Introduction or Results section, etc).

    To achieve this, follow this workflow:
    1. Analyze the rough set of instructions and/or ideas for the Abstract that the user
    provided;
    2. Analyze the current draft of the manuscript;
    3. Draft a new Abstract or edit an existing one following the guidelines below.

    # Current draft of the Abstract (might be empty)
    ```
    {abstract}
    ```

    # Rough instructions from the user to draft or edit the Abstract
    ```
    {instructions_abstract}
    ```

    # Current draft of important manuscript sections (might be empty)
    ```
    {title}
    
    {introduction}

    {results}
    
    {discussion}
    ```

    # Guidelines for the Abstract
    ```
    * The abstract is, for most readers, the only part of the paper that will be 
    read. This means that the abstract must convey the entire message of the paper 
    effectively. To serve this purpose, the abstract’s structure is highly conserved. 
    Each of the Context-Content-Conclusion scheme (C-C-C) elements is detailed below.
    
    * The context must communicate to the reader what gap the paper will fill. The 
    first sentence orients the reader by introducing the broader field in which the 
    particular research is situated. Then, this context is narrowed until it lands on 
    the open question that the research answered. A successful context section sets 
    the stage for distinguishing the paper’s contributions from the current state of 
    the art by communicating what is missing in the literature (i.e., the specific 
    gap) and why that matters (i.e., the connection between the specific gap and the 
    broader context that the paper opened with).

    * The content (“Here we”) first describes the novel method or approach that you 
    used to fill the gap or question. Then you present the meat—your executive 
    summary of the results.

    * Finally, the conclusion interprets the results to answer the question that was 
    posed at the end of the context section. There is often a second part to the 
    conclusion section that highlights how this conclusion moves the broader field 
    forward (i.e., “broader significance”). This is particularly true for more 
    “general” journals with a broad readership.

    * The broad-narrow-broad structure allows you to communicate with a wider 
    readership (through breadth) while maintaining the credibility of your claim (
    which is always based on a finite or narrow set of results).
    ```

    # Output
    Output only the Abstract. If not specified, use Markdown for formatting (if needed).
    Do not provide any explanation.
    """.strip(),
    before_agent_callback=prepare_instructions,
    # output_key="results",
)


async def call_abstract_agent(
        question: str,
        tool_context: ToolContext,
):
    """Tool to call the abstract_agent."""
    section_key = ABSTRACT_KEY
    agent_obj = abstract_agent

    agent_tool = AgentTool(
        agent=agent_obj,
        # skip_summarization=True,
    )

    agent_output = await agent_tool.run_async(
        # args={"request": question},
        args={"request": "Follow your original instructions."},
        tool_context=tool_context,
    )
    # save results
    tool_context.state[section_key] = agent_output

    # remove current instructions since we already applied them
    if section_key in tool_context.state[INSTRUCTIONS_KEY]:
        del tool_context.state[INSTRUCTIONS_KEY][section_key]
    tool_context.state[f"{INSTRUCTIONS_KEY}_{section_key}"] = ""

    return agent_output





discussion_agent = Agent(
    name="discussion_agent",
    model=LiteLlm(model=MODEL_NAME),
    include_contents="none",
    description="Agent expert in drafting or editing the Discussion section of a scientific manuscript.",
    instruction="""
    You are an expert in drafting or editing the Discussion section of a scientific manuscript.
    Your goal is to either:
    1) Draft the Discussion from scratch: if there is no current draft of the Discussion,
    you will draft a Discussion from scratch using the user's instructions below and any
    other relevant section of the manuscript;
    2) Edit an existing Discussion: if there is a current draft of the Discussion,
    you will edit it using the user's instructions below and any
    other relevant section of the manuscript;

    Below you'll find the current draft of the Discussion (if present), a rough set of
    instructions from the user on how to draft it from scratch or edit an existing Discussion,
    the guidelines that you have to follow to correctly structure the Discussion,
    and any other parts of the manuscript that might be relevant for you (such as the current
    draft of the Introduction or Results section, etc).

    To achieve this, follow this workflow:
    1. Analyze the rough set of instructions and/or ideas for the Discussion that the user
    provided;
    2. Analyze the current draft of the manuscript;
    3. Draft a new Discussion or edit an existing one following the guidelines below.

    # Current draft of the Discussion (might be empty)
    ```
    {discussion}
    ```

    # Rough instructions from the user to draft or edit the Discussion
    ```
    {instructions_discussion}
    ```

    # Current draft of important manuscript sections (might be empty)
    ```
    {title}
    
    {abstract}

    {introduction}

    {results}
    ```

    # Guidelines for the Discussion
    ```
    * The discussion section explains how the results have filled the gap that was 
    identified in the introduction, provides caveats to the interpretation, 
    and describes how the paper advances the field by providing new opportunities. 
    This is typically done by recapitulating the results, discussing the limitations, 
    and then revealing how the central contribution may catalyze future progress.
    
    * The first discussion paragraph is special in that it generally summarizes the 
    important findings from the results section. Some readers skip over substantial 
    parts of the results, so this paragraph at least gives them the gist of that 
    section.
    
    * Each of the following paragraphs in the discussion section starts by describing 
    an area of weakness or strength of the paper. It then evaluates the strength or 
    weakness by linking it to the relevant literature. Discussion paragraphs often 
    conclude by describing a clever, informal way of perceiving the contribution or 
    by discussing future directions that can extend the contribution.

    * For example, the first paragraph may summarize the results, focusing on their 
    meaning. The second through fourth paragraphs may deal with potential weaknesses 
    and with how the literature alleviates concerns or how future experiments can 
    deal with these weaknesses. The fifth paragraph may then culminate in a 
    description of how the paper moves the field forward. Step by step, the reader 
    thus learns to put the paper’s conclusions into the right context.
    ```

    # Output
    Output only the Discussion section. If not specified, use Markdown for formatting.
    Do not provide any explanation.
    """.strip(),
    before_agent_callback=prepare_instructions,
    # output_key="results",
)


async def call_discussion_agent(
        question: str,
        tool_context: ToolContext,
):
    """Tool to call the discussion_agent."""
    section_key = DISCUSSION_KEY
    agent_obj = discussion_agent

    agent_tool = AgentTool(
        agent=agent_obj,
        # skip_summarization=True,
    )

    agent_output = await agent_tool.run_async(
        # args={"request": question},
        args={"request": "Follow your original instructions."},
        tool_context=tool_context,
    )
    # save results
    tool_context.state[section_key] = agent_output

    # remove current instructions since we already applied them
    if section_key in tool_context.state[INSTRUCTIONS_KEY]:
        del tool_context.state[INSTRUCTIONS_KEY][section_key]
    tool_context.state[f"{INSTRUCTIONS_KEY}_{section_key}"] = ""

    return agent_output


methods_agent = Agent(
    name="methods_agent",
    model=LiteLlm(model=MODEL_NAME),
    include_contents="none",
    description="Agent expert in drafting or editing the Methods section of a scientific manuscript.",
    instruction="""
    You are an expert in drafting or editing the Methods section of a scientific manuscript.
    Your goal is to either:
    1) Draft the Methods from scratch: if there is no current draft of the Methods,
    you will draft a Methods from scratch using the user's instructions below and any
    other relevant section of the manuscript;
    2) Edit an existing Methods: if there is a current draft of the Methods,
    you will edit it using the user's instructions below and any
    other relevant section of the manuscript;

    Below you'll find the current draft of the Methods (if present), a rough set of
    instructions from the user on how to draft it from scratch or edit an existing Methods,
    the guidelines that you have to follow to correctly structure the Methods,
    and any other parts of the manuscript that might be relevant for you (such as the current
    draft of the Results section, etc).

    To achieve this, follow this workflow:
    1. Analyze the rough set of instructions and/or ideas for the Methods that the user
    provided;
    2. Analyze the current draft of the manuscript;
    3. Draft a new Methods or edit an existing one following the guidelines below.

    # Current draft of the Methods (might be empty)
    ```
    {methods}
    ```

    # Rough instructions from the user to draft or edit the Methods
    ```
    {instructions_methods}
    ```

    # Current draft of important manuscript sections (might be empty)
    ```
    {title}

    {abstract}

    {results}
    ```

    # Guidelines for the Methods
    ```
    * The methods section of a research paper provides the information by which a 
    study's validity is judged. Therefore, it requires a clear and precise 
    description of how an experiment was done, and the rationale for why specific 
    experimental procedures were chosen. The methods section should describe what was 
    done to answer the research question, describe how it was done, justify the 
    experimental design, and explain how the results were analyzed.
    
    * The structure of the Methods section depends on the type of paper. Some potential
    subsections are described below (but they might not be needed in all types manuscript): 
    
        * Overview of Study Design. Briefly state the overall approach (e.g., randomized 
        controlled trial, observational cohort, in vitro assay). Highlight essential 
        design elements—prospective vs. retrospective, parallel vs. crossover, controlled 
        vs. uncontrolled.
        
        * Datasets, participants, samples. Population: inclusion/exclusion criteria, 
        recruitment source. Sample size: justification or power calculation. Ethics: 
        IRB/IACUC approval number and informed‐consent procedures. Source: vendors, 
        catalog numbers, lot numbers. Preparation: any pre‐treatment, storage 
        conditions, handling.
        
        * Equipment and Reagents. Instrumentation: make/model, software versions. 
        Reagents: manufacturer, purity, concentrations/preparation. If multiple 
        assays, group reagents by assay in subsections.
        
        * Procedures and Protocols. Structure this in chronological order or by 
        logical grouping: Primary Intervention or Treatment (Dose, timing, 
        administration route). Data Collection Steps (Behavioral tasks, 
        sample collection times, imaging parameters). Quality Control (
        Blinding/randomization methods; Calibration, validation of equipment). Use 
        sub-headings or numbered lists so each step is clear.
        
        * Data Analysis. Statistical methods: specify tests (e.g., ANOVA, 
        regression), software (e.g., R 4.2, SPSS v28). Handling of missing data: 
        imputation methods, exclusions. Significance thresholds: alpha level, 
        multiple comparisons correction.
        
        * Reproducibility and Transparency. Data availability: repositories, 
        accession numbers. Code availability: scripts, version control links. 
        Protocol registration: clinicaltrials.gov ID or preregistration DOI.
        
    * Style and Tone Tips: Past tense (e.g., “Samples were incubated…”). Precision: 
    give exact volumes, times, and temperatures. Clarity: avoid jargon; define any 
    uncommon abbreviation at first use. Self-contained: every reagent or piece of 
    equipment needed to reproduce should be listed here or in a table.
    ```

    # Output
    Output only the Methods section. If not specified, use Markdown for formatting.
    Do not provide any explanation.
    """.strip(),
    before_agent_callback=prepare_instructions,
    # output_key="results",
)


async def call_methods_agent(
        question: str,
        tool_context: ToolContext,
):
    """Tool to call the methods_agent."""
    section_key = METHODS_KEY
    agent_obj = methods_agent

    agent_tool = AgentTool(
        agent=agent_obj,
        # skip_summarization=True,
    )

    agent_output = await agent_tool.run_async(
        # args={"request": question},
        args={"request": "Follow your original instructions."},
        tool_context=tool_context,
    )
    # save results
    tool_context.state[section_key] = agent_output

    # remove current instructions since we already applied them
    if section_key in tool_context.state[INSTRUCTIONS_KEY]:
        del tool_context.state[INSTRUCTIONS_KEY][section_key]
    tool_context.state[f"{INSTRUCTIONS_KEY}_{section_key}"] = ""

    return agent_output


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
    agent_tool = AgentTool(
        agent=manuscript_assembler_agent,
        # skip_summarization=True,
    )

    agent_output = await agent_tool.run_async(
        # args={"request": question},
        args={"request": "Follow your original instructions."},
        tool_context=tool_context,
    )
    # tool_context.state["introduction"] = agent_output
    return agent_output


manuscript_builder_coordinator_agent = Agent(
    name="manuscript_builder_coordinator_agent",
    model=LiteLlm(model=MODEL_NAME),
    description="Agent expert in coordinating a scientific manuscript writing team to "
                "draft from scratch or edit a scientific manuscript given instructions "
                "from the user.",
    instruction=f"""
    You are an expert in coordinating a team to write a scientific manuscript that is composed
    of different sections such as Title, Abstract, Introduction, Results, Discussion,
    Methods, etc.
    Your ONLY goal is to coordinate a team of agents/tools with specific skills to draft or edit a scientific
    manuscript.
    This is your team of agents/tools:
    * 'request_interpreter_agent': it help you interpret the user's input and extract
    from it the user's subrequests/ideas that are specific to each section of the manuscript.
    Some user's requests/ideas might not be specific to one section but instead impact
    different sections of the manuscript such as the Title, Abstract and Introduction.
    Always forward to this agent/tool the user's message exactly as you received it (which
    can be plain text, Markdown or LaTeX). This agent will return a JSON object with the
    manuscript's sections as keys and the subrequests/ideas for each section as values.
    If the value for a key/section is not empty, it means that the user has a requested changes for
    that section, and you should call a specialized agent to draft that section.
    * 'title_agent': it helps you draft or edit the Title of the
    manuscript. You should always call this agent if the user has
    requested changes that impact this section.
    * 'abstract_agent': it helps you draft or edit the Abstract of the
    manuscript. You should always call this agent if the user has
    requested changes that impact this section.
    * 'introduction_agent': it helps you draft or edit the Introduction section of the
    manuscript. You should always call this agent if the user has
    requested changes that impact this section.
    * 'results_agent': it helps you draft or edit the Results section of the
    manuscript. You should always call this agent if the user has
    requested changes that impact this section.
    * 'discussion_agent': it helps you draft or edit the Discussion section of the
    manuscript. You should always call this agent if the user has
    requested changes that impact this section.
    * 'methods_agent': it helps you draft or edit the Methods section of the
    manuscript. You should always call this agent if the user has
    requested changes that impact this section.
    * `manuscript_assembler_agent`: it helps you assemble the final manuscript with all its
    sections after they have been drafted/edited by other agents.
    
    Follow this workflow:
    1. If the user's input IS NOT related to drafting/editing a scientific manuscript, then
    simply disregard the request politely, state what's your goal and quit. Otherwise,
    continue.
    2. Interpret what the user's requesting from the latest user messages. If more context
    is lacking, try to improve the user's request by adding more context (such as which sections
    of the manuscript might be affected by the requests).
    3. Call the 'request_interpreter_agent' by providing what the user wants for the
    manuscript. This agent will return a JSON object with manuscript section names
    as keys and requests/ideas for that section as values.
    4. Analyze this JSON object. If the value for a section is not
    empty, it means that there are requests for that section that need to be completed, so
    you have to call the section-specific agent to draft it (next step). If none of the sections have
    requests, then your response is to ask the user for more specific requests/edits and quit.
    Otherwise, continue.
    5. For each section that has requests, call the section-specific agent that you have
    available to draft it, such as 'introduction_agent', 'results_agent', etc. NEVER draft/edit
    yourself, you rely on your agents/tools to write any part of the manuscript.
    6. Once all sections (for which you have agents for) are drafted/edited,
    you have to call the 'manuscript_assembler_agent' at the end and ALWAYS show the returned value
    (a full manuscript draft) to the user. Please DO NOT EDIT/CHANGE
    IN ANY WAY this manuscript draft, just show it to the user.
    """.strip(),
    tools=[
        call_request_interpreter_agent,
        call_title_agent,
        # call_keywords_agent,
        call_abstract_agent,
        call_introduction_agent,
        call_results_agent,
        call_discussion_agent,
        call_methods_agent,
        call_manuscript_assembler_agent,
    ],
)

# def exit_loop(tool_context: ToolContext):
#   """Call this function ONLY when the critique indicates no further changes are needed, signaling the iterative process should end."""
#   print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
#   tool_context.actions.escalate = True
#   # Return empty dict as tools should typically return JSON-serializable output
#   return {}
# 
# wf_manuscript_builder_coordinator_agent = SequentialAgent(
#     sub_agents=[
#         call_request_interpreter_agent,
#         call_results_agent,
#         call_introduction_agent,
#         call_discussion_agent,
#     ]
# )

root_agent = manuscript_builder_coordinator_agent
