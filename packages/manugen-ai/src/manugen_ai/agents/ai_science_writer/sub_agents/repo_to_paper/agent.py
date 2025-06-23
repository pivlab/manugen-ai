"""
An agentic workflow that
is provided a file contents or a source code repository,
generates content for a paper, and then revises that content.
"""

from __future__ import annotations

import os

from google.adk.agents import (
    Agent,
    SequentialAgent,
)
from google.adk.tools import FunctionTool
from manugen_ai.tools.tools import clone_repository, read_path_contents
from manugen_ai.utils import get_llm

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")
LLM = get_llm(MODEL_NAME)
COMPLETION_PHRASE = "All the way finished!"

agent_code_summarizer = Agent(
    model=LLM,
    name="agent_code_summarizer",
    description=("I am an intelligent and experienced research software engineer."),
    instruction="""
You are a helpful assistant who helps with cloning and
summarizing research software content from a local
repository. Decide when a tool call is
needed based on the instructions provided.
You have advanced scientific knowledge and
research software engineering skills.
Don't return the results until you have completed all steps.
Only use tools if they exist.
Don't provide me with code you expect me to run.

** repository URL **
See the user prompt for the repository URL.

Steps:
1. clone the repo provided by the user using tool: clone_repository.
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

agent_school = Agent(
    model=LLM,
    name="agent_school",
    description=(
        """
        I am a scientific writing expert with many
        years of experience writing content.
        """
    ),
    instruction="""
You are a helpful assistant.
Your job is to go to school and learn how to
write better scientific papers.
We can do this by understanding a paper:
"Ten simple rules for structuring papers"
https://doi.org/10.1371/journal.pcbi.1005619

We need to summarize the best practices when it comes to writing
these types of papers so we can inform another agent.
Add some bullets of guidance so we may use your synthesis
as another perspective on the relevant topics.
Only provide guidance and don't add other extraneous content.
""",
    output_key="school_thoughts",
)

agent_writer = Agent(
    model=LLM,
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
content for a scientific paper covering the content
we've investigated earlier.
Only use tools if they exist.

Use the following guidance from another helpful agent
in performing your written work:
{school_thoughts}

Here are the content summaries you have to work with.
If either of these are blank or state that there is nothing
available you should ignore the input when writing.

Code:
```
{code_summary}
```

Steps:
1. Once you have read the summary of the content, provide me an scientific
paper content for this project.
The content must be content and not feedback on the code or repository.
The content must be in markdown format!
I'm looking for a scientific paper content, not a code or content review.
The audience of the new content are people who don't yet know about the focus.
Because it's a scientific paper we need to focus on making the content
clear, accurate, and truthful to what the content represents.
For example, don't state that the project does things that it doesn't do
(don't guess! make your writing be related about what the code actually does).
To that point, please do not hallucinate aspects or foci which don't exist in the content.
Also, don't try to execute any code or run it, just provide content.
Don't make queries for code outside of the URL provided by the user.
Please please please don't provide me with code or nit-picky content review.
Only include the markdown content and not extra dialogue about what you're doing or why.
""",
    output_key="content",
)

# sequence for gathering and creating initial content
sequence_writer = SequentialAgent(
    name="writer",
    sub_agents=[agent_school, agent_writer],
)

# sequence for orchestrating everything together
root_agent = SequentialAgent(
    name="repo_agent",
    sub_agents=[agent_code_summarizer, sequence_writer],
    description="""
        Gathers content, writes an initial document,
        and then iteratively refines it with critique loop.
        """,
)
