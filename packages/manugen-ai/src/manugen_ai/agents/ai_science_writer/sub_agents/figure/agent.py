import os
import json
from typing import Optional
from copy import deepcopy

from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
from google.adk.models import LlmResponse

from manugen_ai.schema import (
    CURRENT_FIGURE_KEY,
    FIGURES_KEY,
    SingleFigureDescription,
    prepare_instructions,
)

from . import prompt

MODEL_NAME = os.environ.get(
    "MANUGENAI_FIGURE_MODEL_NAME",
    os.environ.get("MANUGENAI_MODEL_NAME"),
)


def postprocess_figure_metadata(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """TODO: update."""

    if not llm_response.content or not llm_response.content.parts:
        return None

    state = callback_context.state

    original_text = llm_response.content.parts[0].text
    original_json = json.loads(original_text)

    current_figure_id = 1
    if FIGURES_KEY in state:
        current_figure_id = len(state[FIGURES_KEY]) + 1
    
    original_json["id"] = current_figure_id
    modified_text = json.dumps(original_json)

    # TODO: update
    # Create a NEW LlmResponse with the modified content
    # Deep copy parts to avoid modifying original if other callbacks exist
    modified_parts = [deepcopy(part) for part in llm_response.content.parts]
    modified_parts[0].text = modified_text
    
    return LlmResponse(
         content=types.Content(role="model", parts=modified_parts),
         grounding_metadata=llm_response.grounding_metadata
     )

def postprocess_figure_states(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    TODO: add
    """
    state = callback_context.state

    if CURRENT_FIGURE_KEY not in state:
        return None

    current_figure = state[CURRENT_FIGURE_KEY]

    if FIGURES_KEY not in state:
        state[FIGURES_KEY] = {}

    current_figure_state = state[FIGURES_KEY]
    current_figure_state[current_figure["id"]] = {
        k: v for k, v in current_figure.items() if k != "id"
    }

    state[FIGURES_KEY] = current_figure_state

    state[CURRENT_FIGURE_KEY] = ""

    return None


figure_agent = Agent(
    name="figure_agent",
    model=LiteLlm(model=MODEL_NAME),
    # include_contents="none",
    description="Agent expert in interpreting figures of a scientific article.",
    instruction=prompt.PROMPT,
    before_agent_callback=prepare_instructions,
    after_model_callback=postprocess_figure_metadata,
    after_agent_callback=postprocess_figure_states,
    output_schema=SingleFigureDescription,
    output_key=CURRENT_FIGURE_KEY,
)
