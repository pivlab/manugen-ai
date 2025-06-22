import os

from google.adk.agents import LlmAgent
from manugen_ai.schema import ManuscriptStructure
from manugen_ai.utils import get_llm

from . import prompt

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")
LLM = get_llm(
    MODEL_NAME,
    response_format=ManuscriptStructure,
)
model_api_base = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")

if MODEL_NAME.startswith(("ollama",)):
    MODEL_NAME = MODEL_NAME.replace("ollama", "openai")

    if not model_api_base.endswith("/v1"):
        model_api_base += "/v1"

    os.environ["OPENAI_API_BASE"] = model_api_base
    os.environ["OPENAI_API_KEY"] = "unused"

request_interpreter_agent = LlmAgent(
    name="request_interpreter_agent",
    model=LLM,
    include_contents="none",
    description="Interprets the user's input/request, extracts subrequests/ideas from it and assign them to specific sections of the scientific manuscript.",
    instruction=prompt.PROMPT,
    output_schema=ManuscriptStructure,
    output_key="instructions",
)
