import logging
from typing import AsyncGenerator
from typing_extensions import override

from google.adk.agents import LlmAgent, BaseAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from manugen_ai.schema import INSTRUCTIONS_KEY, TITLE_KEY, ABSTRACT_KEY, \
    INTRODUCTION_KEY, RESULTS_KEY, DISCUSSION_KEY, METHODS_KEY

from ..introduction import introduction_agent
from ..results import results_agent
from ..title import title_agent
from ..abstract import abstract_agent
from ..discussion import discussion_agent
from ..methods import methods_agent

from google.adk.agents.callback_context import CallbackContext
from google.genai import types # For types.Content
from typing import Optional

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def manuscript_assembler(callback_context: CallbackContext) -> Optional[types.Content]:
    state = callback_context.state.to_dict()
    manuscript = f"""
# Title
{state.get('title', 'none')}

# Abstract
{state.get('abstract', 'none')}

# Introduction
{state.get('introduction', 'none')}

# Results
{state.get('results', 'none')}

# Discussion
{state.get('discussion', 'none')}

# Methods
{state.get('methods', 'none')}
    """.strip()

    return types.Content(
        parts=[types.Part(text=manuscript)],
        role="model",
    )


assembler_agent = LlmAgent(
    name="assembler_agent",
    before_agent_callback=manuscript_assembler,
)
