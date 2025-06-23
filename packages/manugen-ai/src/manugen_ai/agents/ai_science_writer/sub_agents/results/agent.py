import os

from google.adk.agents import LlmAgent
from manugen_ai.schema import RESULTS_KEY, prepare_instructions
from manugen_ai.utils import get_llm

from . import prompt

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")
LLM = get_llm(MODEL_NAME)

# model_api_base = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
# if MODEL_NAME.startswith(("ollama",)):
#     MODEL_NAME.replace("ollama", "openai")
#     if not model_api_base.endswith("/v1"):
#         model_api_base += "/v1"
#
#     os.environ["OPENAI_API_BASE"] = model_api_base
#     os.environ["OPENAI_API_KEY"] = "unused"

results_agent = LlmAgent(
    name=f"{RESULTS_KEY}_agent",
    model=LLM,
    include_contents="none",
    description="Agent expert in drafting or editing a Results section of a scientific manuscript.",
    instruction=prompt.PROMPT,
    before_agent_callback=prepare_instructions,
    output_key="results",
)
