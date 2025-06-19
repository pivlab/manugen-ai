import logging
from typing import AsyncGenerator
from typing_extensions import override

from google.adk.agents import LlmAgent, BaseAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from manugen_ai.utils import INSTRUCTIONS_KEY, TITLE_KEY, ABSTRACT_KEY, INTRODUCTION_KEY, RESULTS_KEY, DISCUSSION_KEY, METHODS_KEY

from ..introduction import introduction_agent
from ..results import results_agent
from ..title import title_agent
from ..abstract import abstract_agent
from ..discussion import discussion_agent
from ..methods import methods_agent

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ManuscriptDrafterAgent(BaseAgent):
    """
    Custom agent for drafting a scientific manuscript.

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
        # Create internal agents *before* calling super().__init__
        # loop_agent = LoopAgent(
        #     name="CriticReviserLoop", sub_agents=[critic, reviser], max_iterations=2
        # )
        # sequential_agent = SequentialAgent(
        #     name="SectionsProcessing", sub_agents=[
        #         results_agent,
        #         methods_agent,
        #         introduction_agent,
        #         discussion_agent,
        #         abstract_agent,
        #         title_agent,
        #     ]
        # )

        # # Define the sub_agents list for the framework
        # sub_agents_list = [
        #     # story_generator,
        #     # loop_agent,
        #     sequential_agent,
        # ]

        # Pydantic will validate and assign them based on the class annotations.
        super().__init__(
            name=name,
            title_agent=title_agent,
            abstract_agent=abstract_agent,
            introduction_agent=introduction_agent,
            results_agent=results_agent,
            discussion_agent=discussion_agent,
            methods_agent=methods_agent,
            # sequential_agent=sequential_agent,
            # sub_agents=sub_agents_list, # Pass the sub_agents list directly
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Implements the custom orchestration logic for the story workflow.
        Uses the instance attributes assigned by Pydantic (e.g., self.story_generator).
        """
        logger.info(f"[{self.name}] Starting manuscript drafting workflow.")
    
        # # 1. Initial Story Generation
        # logger.info(f"[{self.name}] Running StoryGenerator...")
        # async for event in self.story_generator.run_async(ctx):
        #     logger.info(f"[{self.name}] Event from StoryGenerator: {event.model_dump_json(indent=2, exclude_none=True)}")
        #     yield event
    
        if INSTRUCTIONS_KEY not in ctx.session.state:
            logger.error(f"[{self.name}] No instructions present. Aborting workflow.")
            return
    
        instructions_state = ctx.session.state.get(INSTRUCTIONS_KEY)
    
        # Introduction
        if INTRODUCTION_KEY in instructions_state:
            logger.info(f"[{self.name}] Running Introduction...")

            async for event in self.introduction_agent.run_async(ctx):
                logger.info(f"[{self.name}] Event from Introduction: {event.model_dump_json(indent=2, exclude_none=True)}")
                yield event

        logger.info(f"[{self.name}] Manuscript state after Introduction: {ctx.session.state.get('introduction')[:50]}")
    
        # Results
        if RESULTS_KEY in instructions_state:
            logger.info(f"[{self.name}] Running Results...")

            async for event in self.results_agent.run_async(ctx):
                logger.info(f"[{self.name}] Event from Results: {event.model_dump_json(indent=2, exclude_none=True)}")
                yield event
    
        logger.info(f"[{self.name}] Manuscript state after Results: {ctx.session.state.get('results')[:50]}")

        # Methods
        if METHODS_KEY in instructions_state:
            logger.info(f"[{self.name}] Running Methods...")
            
            async for event in self.methods_agent.run_async(ctx):
                logger.info(f"[{self.name}] Event from Methods: {event.model_dump_json(indent=2, exclude_none=True)}")
                yield event

        logger.info(f"[{self.name}] Manuscript state after Methods: {ctx.session.state.get('methods')[:50]}")
    
        manuscript = f"""
## Title
{ctx.session.state.get('title', 'none')}

## Abstract
{ctx.session.state.get('abstract', 'none')}

## Introduction
{ctx.session.state.get('introduction', 'none')}

## Results
{ctx.session.state.get('results', 'none')}

## Discussion
{ctx.session.state.get('discussion', 'none')}

## Methods
{ctx.session.state.get('methods', 'none')}
        """.strip()
    
    
        # # 3. Sequential Post-Processing (Grammar and Tone Check)
        # logger.info(f"[{self.name}] Running PostProcessing...")
        # # Use the sequential_agent instance attribute assigned during init
        # async for event in self.sequential_agent.run_async(ctx):
        #     logger.info(f"[{self.name}] Event from PostProcessing: {event.model_dump_json(indent=2, exclude_none=True)}")
        #     yield event
        # 
        # # 4. Tone-Based Conditional Logic
        # tone_check_result = ctx.session.state.get("tone_check_result")
        # logger.info(f"[{self.name}] Tone check result: {tone_check_result}")
        # 
        # if tone_check_result == "negative":
        #     logger.info(f"[{self.name}] Tone is negative. Regenerating story...")
        #     async for event in self.story_generator.run_async(ctx):
        #         logger.info(f"[{self.name}] Event from StoryGenerator (Regen): {event.model_dump_json(indent=2, exclude_none=True)}")
        #         yield event
        # else:
        #     logger.info(f"[{self.name}] Tone is not negative. Keeping current story.")
        #     pass
    
        logger.info(f"[{self.name}] Workflow finished.")
        
        
drafter_agent = ManuscriptDrafterAgent(
    name="drafter_agent",
    title_agent=title_agent,
    abstract_agent=abstract_agent,
    introduction_agent=introduction_agent,
    results_agent=results_agent,
    discussion_agent=discussion_agent,
    methods_agent=methods_agent,
)