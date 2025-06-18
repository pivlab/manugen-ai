"""
Module for storing meta-agents which
enhance base agent capabilities within
google-adk.
"""

from __future__ import annotations

import json
from typing import AsyncGenerator, Optional, Set

from google.adk.agents import Agent, LlmAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from pydantic import PrivateAttr


class ResilientToolAgent(LlmAgent):
    """
    Wraps an LlmAgent to retry on missing‐tool (or similar) errors,
    dynamically removing failed tools and giving the LLM a brief hint
    before retrying.

    On each retry:
    1. Strips out any tools whose names appeared in the exception.
    2. Syncs the new tool list to the wrapped agent.
    3. Prepends a short retry-note to the wrapped agent’s instruction.
    """

    _wrapped: LlmAgent = PrivateAttr()
    _max_retries: int = PrivateAttr()
    _failed_tools: Set[str] = PrivateAttr(default_factory=set)

    def __init__(self, wrapped_agent: LlmAgent, max_retries: int = 3):
        # 1) Initialize this wrapper with the same model, instruction, and tools
        super().__init__(
            model=wrapped_agent.model,
            name=wrapped_agent.name,
            description=wrapped_agent.description,
            instruction=wrapped_agent.instruction,
            tools=list(wrapped_agent.tools),  # copy the tool list
            output_key=wrapped_agent.output_key,
        )
        # 2) Ensure the inner agent sees the exact same tools
        self.tools = wrapped_agent.tools

        self._wrapped = wrapped_agent
        self._max_retries = max_retries
        self._failed_tools = set()

    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        last_exc: Optional[Exception] = None

        for attempt in range(1, self._max_retries + 1):
            if self._failed_tools:
                tools_info = "\n".join(
                    f"- {t.__name__ if '__name__' in dir(t) else t.name}: {getattr(t, 'description', '<no description>')}"
                    for t in self.tools
                )
                # Prepend a retry hint so the LLM knows why it's trying again
                failed_list = ", ".join(self._failed_tools)
                self._wrapped.instruction = (
                    f"(Retry {attempt}/{self._max_retries}: "
                    f"the following tool(s) failed previously: {failed_list}. "
                    "Please choose an alternative approach "
                    "based only on tools which are passed to you.)\n\n"
                    "Available tools:\n"
                    f"{tools_info}\n\n" + self._wrapped.instruction
                )

            try:
                # Delegate execution to the inner agent
                async for event in self._wrapped._run_async_impl(ctx):
                    yield event
                return  # success, exit
            except Exception as e:
                last_exc = e
                msg = str(e)

                # Look for the typical "not found in the tools_dict" pattern
                if any(
                    val in msg
                    for val in [
                        "is not found in the tools_dict.",
                        "got an unexpected keyword argument",
                    ]
                ):
                    self._failed_tools.add(msg)
                    continue  # retry without that tool

                # Any other error should bubble up immediately
                raise

        # If all retries exhausted, re-raise the last exception
        if last_exc:
            raise last_exc  # type: ignore


class SectionWriterAgent(LlmAgent):
    """
    Loops through parse_result['sections'], sets session.state['section'],
    invokes the draft_section agent, and accumulates outputs.
    """

    _draft_agent: Agent = PrivateAttr()

    def __init__(self, draft_agent: Agent):
        super().__init__(
            model=draft_agent.model,
            name=draft_agent.name,
            description=draft_agent.description,
            instruction=draft_agent.instruction,
            tools=draft_agent.tools,
            output_key=draft_agent.output_key,
        )
        self._draft_agent = draft_agent

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        sections = json.loads(ctx.session.state.get("improved_json", {})).get(
            "sections", []
        )
        all_texts: list[str] = []
        for section in sections:
            ctx.session.state["section"] = section
            async for event in self._draft_agent._run_async_impl(ctx):
                yield event
            all_texts.append(ctx.session.state.get("section_text"))
        ctx.session.state["section_texts"] = all_texts


class StopChecker(BaseAgent):
    # these become configurable when you instantiate
    context_variable: str = "stop_state"
    completion_phrase: str = "ALL FINISHED!"

    # optional: a generic name/description
    name: str = "stop_checker"
    description: str = (
        "Stops when the configured context variable signals completion"
    )

    async def _run_async_impl(self, ctx: InvocationContext):
        # pull whatever key you chose out of state
        value = ctx.session.state.get(self.context_variable, "")
        if value.strip() == self.completion_phrase:
            yield Event(
                author=self.name,
                actions=EventActions(escalate=True),
            )