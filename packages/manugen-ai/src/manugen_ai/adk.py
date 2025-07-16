import json
from abc import ABCMeta

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types

from .schema import ErrorResponse


class ManugenAIBaseAgent(BaseAgent, metaclass=ABCMeta):
    """
    Base agent class for Manugen AI with enhanced error handling.
    """

    def error_message(self, ctx: InvocationContext, error_msg: str) -> Event:
        if not error_msg.startswith("ERROR:"):
            error_msg = f"ERROR: {error_msg}"

        return Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=types.Content(
                role="model",
                parts=[
                    types.Part(text=error_msg),
                ],
            ),
        )

    def structured_error_message(
        self, 
        ctx: InvocationContext, 
        error_type: str,
        message: str,
        details: str = "",
        suggestion: str = ""
    ) -> Event:
        """
        Create a structured error response that the UI can parse and display properly.
        
        Args:
            ctx: The invocation context
            error_type: Type of error (e.g., 'model_error', 'agent_error', 'validation_error')
            message: Human-readable error message
            details: Additional error details for debugging
            suggestion: Suggested action for the user
        """
        error_response = ErrorResponse(
            error_type=error_type,
            message=message,
            details=details,
            suggestion=suggestion
        )
        
        # Create a structured JSON response that the frontend can parse
        error_json = error_response.model_dump_json()
        
        return Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=types.Content(
                role="model",
                parts=[
                    types.Part(text=f"MANUGEN_ERROR: {error_json}"),
                ],
            ),
        )

    def get_transfer_to_agent_event(
        self, ctx: InvocationContext, agent: BaseAgent
    ) -> Event:
        return Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=types.Content(
                role="model",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(
                            id="empty",
                            name="transfer_to_agent",
                            response={"result": None},
                        )
                    ),
                ],
            ),
            actions=EventActions(
                transfer_to_agent=agent.name,
            ),
        )
