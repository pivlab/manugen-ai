import logging
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from manugen_ai.schema import INSTRUCTIONS_KEY, ManuscriptStructure

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def manuscript_assembler(callback_context: CallbackContext) -> Optional[types.Content]:
    current_state = callback_context.state.to_dict()

    manuscript_content = ""

    for section_name in ManuscriptStructure.model_json_schema()["properties"].keys():
        instructions_key = f"{INSTRUCTIONS_KEY}_{section_name}"

        if (
            instructions_key in current_state
            and current_state[instructions_key].strip() != ""
        ):
            # if there are current instructions for this section, then include that section
            # in the assembled manuscript
            manuscript_content += f"\n# {section_name.capitalize()}\n\n{current_state.get(section_name)}\n\n"

            # then remove the instruction key from the state
            callback_context.state[instructions_key] = ""

    return types.Content(
        parts=[types.Part(text=manuscript_content)],
        role="model",
    )


assembler_agent = LlmAgent(
    name="assembler_agent",
    description="This is a simple agent that assembles all manuscript section that were drafted in the last request.",
    before_agent_callback=manuscript_assembler,
)
