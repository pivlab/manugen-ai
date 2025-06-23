import logging
from typing import AsyncGenerator

from google.adk.agents import SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from manugen_ai.adk import ManugenAIBaseAgent
from typing_extensions import override

from ..interpreter import request_interpreter_agent
from ..section_drafter import section_drafter_agent

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InputCopyAgent(ManugenAIBaseAgent):
    # model_config allows setting Pydantic configurations if needed, e.g., arbitrary_types_allowed
    model_config = {"arbitrary_types_allowed": True}

    def __init__(self):
        super().__init__(
            name="simple_copy_agent",
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        # FIXME: workaround to test in adk web
        # logger.info(f"User content: {ctx.user_content}")

        last_user_input = ctx.user_content.parts[0]
        if last_user_input.text is not None and last_user_input.text.strip() == "fig":
            last_user_input = ctx.user_content.parts[1]

        ctx.session.state["last_user_input"] = last_user_input.text

        if False:
            yield

        return


input_copy_agent = InputCopyAgent()

manuscript_drafter_agent = SequentialAgent(
    name="manuscript_drafter_agent",
    description="Interpret user's input to identify a request, then assigns that request to a specific manuscript section, and drafts that section",
    sub_agents=[
        input_copy_agent,
        request_interpreter_agent,
        section_drafter_agent,
        # assembler_agent,
    ],
)
