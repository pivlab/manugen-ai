import os
from google.adk.agents import SequentialAgent

from .sub_agents.interpreter import request_interpreter_agent
from .sub_agents.drafter import drafter_agent
from .sub_agents.assembler import assembler_agent

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")
os.environ["OPENAI_API_BASE"] = ""

# when using the openai provider we need a /v1 suffix, so if it doesn't end in /v1, add it
model_api_base = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
if MODEL_NAME.startswith(("ollama",)):
    MODEL_NAME.replace("ollama", "openai")
    if not model_api_base.endswith("/v1"):
        model_api_base += "/v1"

    os.environ["OPENAI_API_BASE"] = model_api_base
    os.environ["OPENAI_API_KEY"] = "unused"

wf_manuscript_builder_coordinator_agent = SequentialAgent(
    name="wf_manuscript_builder_coordinator_agent",
    description="Interpret user's input, drafts manuscript, and shows it",
    sub_agents=[
        request_interpreter_agent,
        drafter_agent,
        assembler_agent,
    ]
)

root_agent = wf_manuscript_builder_coordinator_agent
