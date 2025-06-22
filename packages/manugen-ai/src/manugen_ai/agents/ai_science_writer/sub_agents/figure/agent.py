"""
An agent to interpret scientific figures and generate descriptions.
"""

import os
from copy import deepcopy
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.genai import types
from manugen_ai.schema import (
    CURRENT_FIGURE_KEY,
    FIGURES_KEY,
    SingleFigureDescription,
    prepare_instructions,
)
from manugen_ai.utils import get_llm

from . import prompt

MODEL_NAME = os.environ.get(
    "MANUGENAI_FIGURE_MODEL_NAME",
    os.environ.get("MANUGENAI_MODEL_NAME"),
)
LLM = get_llm(MODEL_NAME)


def process_figure_response(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """TODO: update."""

    if not llm_response.content or not llm_response.content.parts:
        return None

    # get current state
    state = callback_context.state

    # get agent description about figure
    figure_desc = llm_response.content.parts[0].text
    figure_desc_obj = SingleFigureDescription.model_validate_json(figure_desc)

    # compute figure number
    current_figure_id = 1
    if FIGURES_KEY in state:
        current_figure_id = len(state[FIGURES_KEY]) + 1

    figure_desc_obj.figure_number = current_figure_id
    modified_text = figure_desc_obj.model_dump_json()

    # TODO: update
    # Create a NEW LlmResponse with the modified content
    # Deep copy parts to avoid modifying original if other callbacks exist
    modified_parts = [deepcopy(part) for part in llm_response.content.parts]
    modified_parts[0].text = modified_text

    return LlmResponse(
        content=types.Content(role="model", parts=modified_parts),
        grounding_metadata=llm_response.grounding_metadata,
    )


def update_figure_state(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    TODO: add
    """
    state = callback_context.state

    if CURRENT_FIGURE_KEY not in state:
        return None

    current_figure = state[CURRENT_FIGURE_KEY]
    current_figure_obj = SingleFigureDescription.model_validate(current_figure)

    if FIGURES_KEY not in state:
        state[FIGURES_KEY] = {}

    current_figure_state = state[FIGURES_KEY]
    current_figure_state[current_figure_obj.figure_number] = {
        k: v for k, v in current_figure_obj.model_dump().items() if k != "figure_number"
    }

    state[FIGURES_KEY] = current_figure_state

    state[CURRENT_FIGURE_KEY] = ""

    return None


figure_agent = LlmAgent(
    name="figure_agent",
    model=LLM,
    description="Interprets figures of a scientific article by providing a title and description.",
    instruction=prompt.PROMPT,
    before_agent_callback=prepare_instructions,
    after_model_callback=process_figure_response,
    after_agent_callback=update_figure_state,
    output_schema=SingleFigureDescription,
    output_key=CURRENT_FIGURE_KEY,
)
