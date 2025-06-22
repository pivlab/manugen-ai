import logging
from typing import AsyncGenerator, Callable, Iterable

from google.adk.agents import BaseAgent, LlmAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types 
from manugen_ai.schema import (
    INSTRUCTIONS_KEY,
)
from typing_extensions import override

from ..repo_to_paper import root_agent as repo_agent
from ..reviewer import root_agent as review_agent
from ..retraction_avoidance import root_agent as retraction_avoidance_agent
from ..citations import root_agent as citation_agent
from ..manuscript_drafter import manuscript_drafter_agent
from ..figure import figure_agent

from manugen_ai.adk import ManugenAIBaseAgent

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoordinatorAgent(ManugenAIBaseAgent):
    """
    Custom agent for drafting sections of a scientific manuscript.

    This agent orchestrates a sequence of LLM agents to draft the different sections
    of a scientific manuscript.
    """

    # --- Field Declarations for Pydantic ---
    # Declare the agents passed during initialization as class attributes with type hints
    # manuscript_drafter_agent: SequentialAgent
    # figure_agent: LlmAgent

    sub_agents_cond: list[tuple[BaseAgent, Callable]]

    # model_config allows setting Pydantic configurations if needed, e.g., arbitrary_types_allowed
    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        # name: str,
        # manuscript_drafter_agent: SequentialAgent,
        # figure_agent: LlmAgent,
        sub_agents_cond: list[tuple[BaseAgent, Callable]],
    ):
        """
        TODO: update
        
        Initializes the StoryFlowAgent.

        Args:
            sub_agents_cond (list[tuple[BaseAgent, Callable]]): ordered list of agents to call
            TODO: add more
        """

        # Pydantic will validate and assign them based on the class annotations.
        super().__init__(
            name="coordinator_agent",
            # manuscript_drafter_agent=manuscript_drafter_agent,
            # figure_agent=figure_agent,
            sub_agents_cond=sub_agents_cond
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
        if last_user_input.text is not None and last_user_input.text.strip() == "fig":
            last_user_input = ctx.user_content.parts[1]
        
        agent_was_run = False
        
        for agent, agent_condition in self.sub_agents_cond:
            if not agent_condition(last_user_input):
                continue

            yield self.get_transfer_to_agent_event(ctx, agent)
            
            if last_user_input.inline_data is not None:
                # adk does not support 'display_name' in the request for images
                last_user_input.inline_data.display_name = None

            # TODO: check if changing the InvocationContext like this is a good idea
            ctx.user_content.parts = [last_user_input]
            
            # call agent
            async for event in agent.run_async(ctx):
                yield event
            
            agent_was_run = True
            
            # we only run one agent per request
            break
        
        if not agent_was_run:
            yield self.error_message(ctx, "No agent was found for request.")

coordinator_agent = CoordinatorAgent(
    sub_agents_cond=[
        (
            figure_agent,
            lambda user_input: user_input.inline_data is not None and user_input.inline_data.mime_type is not None and user_input.inline_data.mime_type.startswith("image/"),
        ),
        (
            manuscript_drafter_agent,
            lambda user_input: user_input.text is not None and user_input.text != "",
        ),
        (
            retraction_avoidance_agent,
            lambda user_input: user_input.text is not None and "$RETRACTION_AVOIDANCE_REQUEST$" in user_input.text,
        ),
        (
            citation_agent,
            lambda user_input: user_input.text is not None and "$CITATION_REQUEST$" in user_input.text,
        ),
        (
            review_agent,
            lambda user_input: user_input.text is not None and "$REFINE_REQUEST$" in user_input.text,
        ),
        (
            repo_agent,
            lambda user_input: user_input.text is not None and "$REPO_REQUEST$" in user_input.text,
        ),
        (
            manuscript_drafter_agent,
            lambda user_input: user_input.text is not None and user_input.text != ""
        ),
    ],
)
