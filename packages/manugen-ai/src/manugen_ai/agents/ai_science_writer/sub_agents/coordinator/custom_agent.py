import logging
from typing import AsyncGenerator, Callable

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from manugen_ai.adk import ManugenAIBaseAgent
from typing_extensions import override

from ..citations import root_agent as citation_agent
from ..figure import figure_agent
from ..manuscript_drafter import manuscript_drafter_agent
from ..repo_to_paper import root_agent as repo_agent
from ..retraction_avoidance import root_agent as retraction_avoidance_agent
from ..reviewer import root_agent as review_agent

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoordinatorAgent(ManugenAIBaseAgent):
    """
    Custom agent for drafting sections of a scientific manuscript.

    This agent orchestrates a sequence of LLM agents to draft the different sections
    of a scientific manuscript. Enhanced with proper error handling to provide
    meaningful feedback to users.
    """

    sub_agents_cond: list[tuple[BaseAgent, Callable]]
    """Sub agents and their conditions to be run. If conditions are met, the agent is run.
    Conditions are tested in the same order in the list.
    """

    model_config = {"arbitrary_types_allowed": True}
    """The pydantic model config."""

    def __init__(
        self,
        sub_agents_cond: list[tuple[BaseAgent, Callable]],
    ):
        super().__init__(
            name="coordinator_agent",
            sub_agents_cond=sub_agents_cond,
        )

    def _extract_error_details(self, exception: Exception) -> tuple[str, str, str]:
        """
        Extract error details from an exception to provide better user feedback.
        
        Returns:
            tuple: (error_type, message, suggestion)
        """
        error_str = str(exception).lower()
        
        # Check for common error patterns
        if "ollama" in error_str and ("not found" in error_str or "pull" in error_str):
            return (
                "model_error",
                "The selected AI model is not available.",
                "Please check your .env file and ensure the specified Ollama model has been pulled. You can pull the model using: ollama pull <model_name>"
            )
        elif "connection" in error_str or "timeout" in error_str:
            return (
                "connection_error", 
                "Unable to connect to the AI service.",
                "Please check that the AI service (Ollama, OpenAI, etc.) is running and accessible."
            )
        elif "api key" in error_str or "unauthorized" in error_str:
            return (
                "auth_error",
                "Authentication failed with the AI service.",
                "Please check your API keys in the .env file."
            )
        elif "rate limit" in error_str:
            return (
                "rate_limit_error",
                "Too many requests to the AI service.",
                "Please wait a moment before trying again."
            )
        else:
            return (
                "agent_error",
                "An error occurred while processing your request.",
                "Please try again. If the problem persists, check the logs for more details."
            )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Implements own core agent logic. The coordinator agent runs only one agent per
        request. Enhanced with comprehensive error handling.
        """
        logger.info(f"[{self.name}] Starting Coordinator workflow.")
        logger.info(ctx.user_content)

        try:
            # get the latest user's message
            last_user_input = ctx.user_content.parts[0]

            # FIXME: workaround to test in adk web
            #  skip latest user message if it has text "fig"
            #  adk web forces to send a text message as well, which should be always "fig"
            #  for it to work here.
            if last_user_input.text is not None and last_user_input.text.strip() == "fig":
                last_user_input = ctx.user_content.parts[1]

            agent_was_run = False

            # iterate over the list of subagents and their conditions to run
            for agent, agent_condition in self.sub_agents_cond:
                if not agent_condition(last_user_input):
                    continue

                # simulate an event that there was a transfer of agent
                yield self.get_transfer_to_agent_event(ctx, agent)

                # remove "display_name" since adk does not support it
                if last_user_input.inline_data is not None:
                    last_user_input.inline_data.display_name = None

                try:
                    # call agent with error handling
                    async for event in agent.run_async(ctx):
                        yield event
                    
                    agent_was_run = True
                    # we only run one agent per request
                    break
                    
                except Exception as e:
                    logger.error(f"[{self.name}] Error in sub-agent {agent.name}: {str(e)}", exc_info=True)
                    
                    # Extract meaningful error information
                    error_type, message, suggestion = self._extract_error_details(e)
                    
                    yield self.structured_error_message(
                        ctx,
                        error_type=error_type,
                        message=message,
                        details=f"Error in {agent.name}: {str(e)}",
                        suggestion=suggestion
                    )
                    
                    agent_was_run = True
                    break

            if not agent_was_run:
                yield self.structured_error_message(
                    ctx,
                    error_type="validation_error",
                    message="No suitable agent found for your request.",
                    suggestion="Please check your input format or try a different type of request."
                )
                
        except Exception as e:
            logger.error(f"[{self.name}] Unexpected error in coordinator: {str(e)}", exc_info=True)
            
            yield self.structured_error_message(
                ctx,
                error_type="system_error",
                message="An unexpected system error occurred.",
                details=str(e),
                suggestion="Please try again. If the problem persists, contact support."
            )


coordinator_agent = CoordinatorAgent(
    sub_agents_cond=[
        (
            figure_agent,
            lambda user_input: user_input.inline_data is not None
            and user_input.inline_data.mime_type is not None
            and user_input.inline_data.mime_type.startswith("image/"),
        ),
        (
            retraction_avoidance_agent,
            lambda user_input: user_input.text is not None
            and "$RETRACTION_AVOIDANCE_REQUEST$" in user_input.text,
        ),
        (
            citation_agent,
            lambda user_input: user_input.text is not None
            and "$CITATION_REQUEST$" in user_input.text,
        ),
        (
            review_agent,
            lambda user_input: user_input.text is not None
            and "$REFINE_REQUEST$" in user_input.text,
        ),
        (
            repo_agent,
            lambda user_input: user_input.text is not None
            and "$REPO_REQUEST$" in user_input.text,
        ),
        (
            manuscript_drafter_agent,
            lambda user_input: user_input.text is not None and user_input.text != "",
        ),
    ],
)
