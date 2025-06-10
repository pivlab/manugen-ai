"""
prototyping with google-adk for an agentic workflow that
is provided a source code repository, generates an abstract
for a paper about code, and then revises that content.

Note: this work assumes the use of ollama/llama3.2
which were used as background services outside of this file.
"""

from __future__ import annotations

from google.adk.agents import Agent, LoopAgent, SequentialAgent, LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from manugen_ai.tools.tools import exit_loop, read_path_contents, clone_repository
from manugen_ai.utils import prepare_ollama_llama_for_adk_state

prepare_ollama_llama_for_adk_state()

GENERAL_MODEL_NAME = "openai/qwen3"
CODE_SPECIALIST_MODEL_NAME = "openai/devstral"
COMPLETION_PHRASE = "All the way finished!"

agent_code_summarizer = Agent(
    model=LiteLlm(model=CODE_SPECIALIST_MODEL_NAME),
    name="agent_getter",
    description=("I am an intelligent and experienced research software engineer."),
    instruction="""
You are a helpful assistant who helps with cloning and
summarizing research software content from a local
repository. Decide when a tool call is
needed based on the instructions provided.
You have advanced scientific knowledge and
research software engineering skills.
Don't return the results until you have completed all steps.

** repository URL **
```
{{repository_url}}
```

Steps:
1. clone the repo {{repository_url}} provided by the user using tool: clone_repository.
This tool will provide a temporary directory where you may find the contents.

2. read the contents of the repo from the clone_repository output using tool: read_path_contents
Add the most important contents of the repo to the final result for context in later steps.
Don't make things up about the content that aren't in there, simply return the content as-is.
We need to make sure we don't hallucinate aspects that aren't in the content.
""",
    tools=[
        FunctionTool(func=clone_repository),
        FunctionTool(func=read_path_contents),
    ],
    output_key="code_summary",
)

agent_content_summarizer = Agent(
    model=LiteLlm(model=GENERAL_MODEL_NAME),
    name="agent_content_summarizer",
    description=("I am and intelligent and experienced scientific researcher."),
    instruction="""
Decide when a tool call is
needed based on the instructions provided.
You have advanced scientific knowledge and
research skills.
Don't return the results until you have completed all steps.
You will be provided a path which includes file contents to summarize.

** path to summarize **
```
{{content_path}}
```

Steps:
1. Read the contents of {{content_path}} using tool: read_path_contents
Add the most important contents of the repo to the final result for context in later steps.
Don't make things up about the content that aren't in there, simply return the content as-is.
We need to make sure we don't hallucinate aspects that aren't in the content.
""",
    tools=(FunctionTool(func=read_path_contents),),
    output_key="content_summary",
)

agent_initial_content_coordinator = LlmAgent(
    model=LiteLlm(model=GENERAL_MODEL_NAME),
    name="agent_initial_coordinator",
    description=("I coordinate various tasks leveraging other agents."),
    instruction="""
    Send to the agent_code_summarizer when there's a code url to summarize.
    Send to the agent_content_summarizer when there's a path to summarize.
""",
    sub_agents=[agent_code_summarizer, agent_content_summarizer],
    output_key="full_initial_summary",
)

agent_writer = Agent(
    model=LiteLlm(model=GENERAL_MODEL_NAME),
    name="agent_writer",
    description=(
        """
                 I am a scientific writing expert with many
                 years of experience writing content.
                 """
    ),
    instruction="""
You are a helpful assistant.
Use the information provided by the getter_agent to write an
abstract for a scientific paper covering the content
we've investigated earlier.
This is the content summary you have to work with:
```
{{full_initial_summary}}
```

Steps:
1. Once you have read the summary of the content, provide me an scientific
paper abstract for this project.
The content must be an abstract and not feedback on the code or repository.
The abstract content must be in markdown format!
I'm looking for a scientific paper abstract, not a code or content review.
The audience of the new content are people who don't yet know about the focus.
Because it's a scientific paper we need to focus on making the abstract
clear, accurate, and truthful to what the content represents.
For example, don't state that the project does things that it doesn't do
(don't guess! make your writing be related about what the code actually does).
To that point, please do not hallucinate aspects or foci which don't exist in the content.
Also, don't try to execute any code or run it, just provide an abstract.
Don't make queries for code outside of the URL provided by the user.
Please please please don't provide me with code or nit-picky content review.
Only include the markdown abstract content and not extra dialogue about what you're doing or why.
""",
    output_key="abstract",
)

agent_editor = Agent(
    model=LiteLlm(model=GENERAL_MODEL_NAME),
    name="agent_editor",
    description=("You're a scientific writing editor."),
    instruction=f"""
You are a helpful scientific writing editor who has been
given an abstract to review.
If you exit, please tell me why.

**Document to Review:**
```
{{abstract}}
```

Identify 1-2 *clear and actionable* ways the document could be improved to better capture the topic or enhance reader engagement (e.g., "Needs a stronger opening sentence", "Clarify the character's goal"):
Provide these specific suggestions concisely. Output *only* the critique text.

ELSE IF there is no feedback and the document is coherent, addresses the topic adequately for its length, and has no glaring errors or obvious omissions:
Respond *exactly* with the phrase "{COMPLETION_PHRASE}" and nothing else. It doesn't need to be perfect, just functionally complete for this stage. Avoid suggesting purely subjective stylistic preferences if the core is sound.
Use only tools you need to use after completing the critique.
Use no tool calls besides exit_loop.
""",
    output_key="critique",
)

agent_refiner = Agent(
    model=LiteLlm(model=GENERAL_MODEL_NAME),
    name="agent_refiner",
    description=("You're a scientific writing expert."),
    instruction=f"""
You are a helpful scientific writing expert.
You have advanced scientific knowledge and
research software engineering skills.

**Current Document:**
```
{{abstract}}
```
**Critique/Suggestions:**
```
{{critique}}
```

**Task:**
Analyze the 'Critique/Suggestions'.
IF the critique is *exactly* "{COMPLETION_PHRASE}":
You MUST call the 'exit_loop' function. Do not output any text.
ELSE (the critique contains actionable feedback):
Carefully apply the suggestions to improve the 'Current Document'. Output *only* the refined document text.

Do not add explanations. Either output the refined document OR call the exit_loop function.

""",
    tools=[FunctionTool(func=exit_loop)],
    output_key="abstract",
)

# sequence for gathering and creating initial content
sequence_get_content = SequentialAgent(
    name="WriterSequence",
    sub_agents=[agent_initial_content_coordinator, agent_writer],
)

# loop for refining the initial content
loop_refinement = LoopAgent(
    name="RefinementLoop",
    sub_agents=[agent_editor, agent_refiner],
    max_iterations=10,
)

# sequence for orchestrating everything together
root_agent = SequentialAgent(
    name="root_agent",
    sub_agents=[sequence_get_content, loop_refinement],
    description="Writes an initial document and then iteratively refines it with critique loop.",
)
