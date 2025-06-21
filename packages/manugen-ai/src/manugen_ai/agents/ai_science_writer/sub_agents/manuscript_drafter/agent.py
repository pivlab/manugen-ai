from google.adk.agents import SequentialAgent

from ..assembler import assembler_agent
from ..interpreter import request_interpreter_agent
from ..section_drafter import section_drafter_agent

manuscript_drafter_agent = SequentialAgent(
    name="manuscript_drafter_agent",
    description="Interpret user's input, drafts all sections of the manuscript, and then assembles the manuscript it",
    sub_agents=[
        request_interpreter_agent,
        section_drafter_agent,
        assembler_agent,
    ],
)
