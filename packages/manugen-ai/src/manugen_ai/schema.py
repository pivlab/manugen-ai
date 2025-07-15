from __future__ import annotations

from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from pydantic import BaseModel, Field


def prepare_instructions(callback_context: CallbackContext) -> Optional[types.Content]:
    current_state = callback_context.state.to_dict()

    for key1 in ManuscriptStructure.model_json_schema()["properties"].keys():
        # set instructions for each manuscript section
        if (
            INSTRUCTIONS_KEY in current_state
            and key1 in current_state[INSTRUCTIONS_KEY]
        ):
            callback_context.state[f"{INSTRUCTIONS_KEY}_{key1}"] = current_state[
                INSTRUCTIONS_KEY
            ][key1]

        # if there is no draft for this section, assign empty string
        if key1 not in callback_context.state:
            callback_context.state[key1] = ""

    # add figures descriptions
    figure_descriptions = ""
    if FIGURES_KEY in current_state:
        current_figure_state = current_state[FIGURES_KEY]
        for figure_number, figure_data in current_figure_state.items():
            figure_descriptions += f"Figure {figure_number}: {figure_data['title']}\n{figure_data['description']}\n\n"

    callback_context.state[FIGURES_DESCRIPTIONS_KEY] = figure_descriptions.strip()


class ManuscriptStructure(BaseModel):
    title: str = Field(default="")
    # keywords: str = Field(default="")
    abstract: str = Field(default="")
    introduction: str = Field(default="")
    results: str = Field(default="")
    discussion: str = Field(default="")
    methods: str = Field(default="")


INSTRUCTIONS_KEY = "instructions"
TITLE_KEY = "title"
ABSTRACT_KEY = "abstract"
INTRODUCTION_KEY = "introduction"
RESULTS_KEY = "results"
DISCUSSION_KEY = "discussion"
METHODS_KEY = "methods"


class SingleFigureDescription(BaseModel):
    figure_number: int = Field(default=0)
    title: str = Field(default="")
    description: str = Field(default="")


CURRENT_FIGURE_KEY = "current_figure"
FIGURES_KEY = "figures"
FIGURES_DESCRIPTIONS_KEY = "figures_descriptions"


class ErrorResponse(BaseModel):
    """Standardized error response structure for the UI."""
    error: bool = Field(default=True)
    error_type: str = Field(description="Type of error (e.g., 'model_error', 'agent_error', 'validation_error')")
    message: str = Field(description="Human-readable error message")
    details: str = Field(default="", description="Additional error details for debugging")
    suggestion: str = Field(default="", description="Suggested action for the user")
