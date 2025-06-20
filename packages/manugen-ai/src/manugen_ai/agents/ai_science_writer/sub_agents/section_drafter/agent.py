import logging
from typing import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from manugen_ai.schema import (
    INSTRUCTIONS_KEY,
)
from typing_extensions import override

from ..abstract import abstract_agent
from ..discussion import discussion_agent
from ..introduction import introduction_agent
from ..methods import methods_agent
from ..results import results_agent
from ..title import title_agent

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SectionDrafterAgent(BaseAgent):
    """
    Custom agent for drafting sections of a scientific manuscript.

    This agent orchestrates a sequence of LLM agents to draft the different sections
    of a scientific manuscript.
    """

    # --- Field Declarations for Pydantic ---
    # Declare the agents passed during initialization as class attributes with type hints
    title_agent: LlmAgent
    abstract_agent: LlmAgent
    introduction_agent: LlmAgent
    results_agent: LlmAgent
    discussion_agent: LlmAgent
    methods_agent: LlmAgent

    # loop_agent: LoopAgent
    # sequential_agent: SequentialAgent

    section_agents_order: list[LlmAgent]

    # model_config allows setting Pydantic configurations if needed, e.g., arbitrary_types_allowed
    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        name: str,
        title_agent: LlmAgent,
        abstract_agent: LlmAgent,
        introduction_agent: LlmAgent,
        results_agent: LlmAgent,
        discussion_agent: LlmAgent,
        methods_agent: LlmAgent,
    ):
        """
        Initializes the StoryFlowAgent.

        Args:
            name: The name of the agent.
            title_agent: An LlmAgent to draft the title of a manuscript.
            abstract_agent: An LlmAgent to draft the abstract of a manuscript.
            introduction_agent: An LlmAgent to draft the introduction of a manuscript.
            results_agent: An LlmAgent to draft the results of a manuscript.
            discussion_agent: An LlmAgent to draft the discussion of a manuscript.
            methods_agent: An LlmAgent to draft the methods of a manuscript.
        """
        section_agents_order = [
            introduction_agent,
            results_agent,
            methods_agent,
            discussion_agent,
            abstract_agent,
            title_agent,
        ]

        # Pydantic will validate and assign them based on the class annotations.
        super().__init__(
            name=name,
            title_agent=title_agent,
            abstract_agent=abstract_agent,
            introduction_agent=introduction_agent,
            results_agent=results_agent,
            discussion_agent=discussion_agent,
            methods_agent=methods_agent,
            section_agents_order=section_agents_order,
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Implements the custom orchestration logic for manuscript drafting workflow.
        """
        logger.info(f"[{self.name}] Starting manuscript drafting workflow.")

        if INSTRUCTIONS_KEY not in ctx.session.state:
            logger.error(f"[{self.name}] No instructions present. Aborting workflow.")
            return

        instructions_state = ctx.session.state.get(INSTRUCTIONS_KEY)

        for section_agent in self.section_agents_order:
            section_key = section_agent.name.split("_")[0]

            if (
                section_key not in instructions_state
                or instructions_state[section_key].strip() == ""
            ):
                continue

            logger.info(f"[{self.name}] Running {section_key}...")

            async for event in section_agent.run_async(ctx):
                logger.info(
                    f"[{self.name}] Event from {section_key}: {event.model_dump_json(indent=2, exclude_none=True)}"
                )
                yield event

        logger.info(f"[{self.name}] Workflow finished.")


section_drafter_agent = SectionDrafterAgent(
    name="section_drafter_agent",
    title_agent=title_agent,
    abstract_agent=abstract_agent,
    introduction_agent=introduction_agent,
    results_agent=results_agent,
    discussion_agent=discussion_agent,
    methods_agent=methods_agent,
)
