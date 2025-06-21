import logging
from typing import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types 
from manugen_ai.schema import (
    INSTRUCTIONS_KEY,
)
from typing_extensions import override

from ..manuscript_drafter import manuscript_drafter_agent
from ..figure import figure_agent

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """
    Custom agent for drafting sections of a scientific manuscript.

    This agent orchestrates a sequence of LLM agents to draft the different sections
    of a scientific manuscript.
    """

    # --- Field Declarations for Pydantic ---
    # Declare the agents passed during initialization as class attributes with type hints
    manuscript_drafter_agent: SequentialAgent
    figure_agent: LlmAgent

    # model_config allows setting Pydantic configurations if needed, e.g., arbitrary_types_allowed
    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        name: str,
        manuscript_drafter_agent: SequentialAgent,
        figure_agent: LlmAgent,
    ):
        """
        TODO: update
        
        Initializes the StoryFlowAgent.

        Args:
            name: The name of the agent.
            TODO: add more
        """

        # Pydantic will validate and assign them based on the class annotations.
        super().__init__(
            name=name,
            manuscript_drafter_agent=manuscript_drafter_agent,
            figure_agent=figure_agent,
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        TODO: update
        """
        logger.info(f"[{self.name}] Starting Coordinator workflow.")
        logger.info(ctx.user_content)
        
        # FIXME: workaround to test in adk web
        last_user_input = ctx.user_content.parts[0]
        if last_user_input.text is not None and len(last_user_input.text.strip()) < 10:
            last_user_input = ctx.user_content.parts[1]
        
        if last_user_input.inline_data is not None and last_user_input.inline_data.mime_type is not None and last_user_input.inline_data.mime_type.startswith("image/"):
            last_user_input.inline_data.display_name = None
            ctx.user_content.parts = [last_user_input]
            
            async for event in self.figure_agent.run_async(ctx):
                yield event
            
        elif last_user_input.text is not None and last_user_input.text != "":
            ctx.user_content.parts = [last_user_input]
            async for event in self.manuscript_drafter_agent.run_async(ctx):
                yield event
        
        # yield Event(
        #     author=self.name,
        #     invocation_id=ctx.invocation_id,
        #     content=types.Content(
        #         role="model",
        #         parts=[
        #             types.Part(text="Just testing :)"),
        #             types.Part(text=f"you said: '{last_user_message}'"),
        #         ]
        #     ),
        # )

        # if INSTRUCTIONS_KEY not in ctx.session.state:
        #     logger.error(f"[{self.name}] No instructions present. Aborting workflow.")
        #     return

        # instructions_state = ctx.session.state.get(INSTRUCTIONS_KEY)
        # 
        # for section_agent in self.section_agents_order:
        #     section_key = section_agent.name.split("_")[0]
        # 
        #     if (
        #         section_key not in instructions_state
        #         or instructions_state[section_key].strip() == ""
        #     ):
        #         continue
        # 
        #     logger.info(f"[{self.name}] Running {section_key}...")
        # 
        #     async for event in section_agent.run_async(ctx):
        #         logger.info(
        #             f"[{self.name}] Event from {section_key}: {event.model_dump_json(indent=2, exclude_none=True)}"
        #         )
        #         yield event
        # 
        # logger.info(f"[{self.name}] Workflow finished.")


coordinator_agent = CoordinatorAgent(
    name="section_drafter_agent",
    manuscript_drafter_agent=manuscript_drafter_agent,
    figure_agent=figure_agent,
)
