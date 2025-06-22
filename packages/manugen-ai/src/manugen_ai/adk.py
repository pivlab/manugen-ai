from abc import ABCMeta

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types

class ManugenAIBaseAgent(BaseAgent, metaclass=ABCMeta):
    """
    TODO: add docs
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

    def get_transfer_to_agent_event(self, ctx: InvocationContext, agent: BaseAgent) -> Event:
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
                            response={"result": None}
                        )
                    ),
                ],
            ),
            actions=EventActions(
                transfer_to_agent=agent.name,
            ),
        )