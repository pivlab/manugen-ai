"""
Module for storing meta-agents which
enhance base agent capabilities within
google-adk.
"""

from __future__ import annotations

import json
from typing import AsyncGenerator

from google.adk.agents import Agent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from pydantic import PrivateAttr


class ResilientToolAgent(LlmAgent):
    """
    Wraps an LlmAgent to retry on missing-tool errors, without renaming the agent.
    """

    _wrapped: LlmAgent = PrivateAttr()
    _max_retries: int = PrivateAttr()

    def __init__(
        self,
        wrapped_agent: LlmAgent,
        max_retries: int = 3,
    ):
        # Initialize as a true LlmAgent with identical identity and tools
        super().__init__(
            model=wrapped_agent.model,
            name=wrapped_agent.name,
            description=wrapped_agent.description,
            instruction=wrapped_agent.instruction,
            tools=wrapped_agent.tools,
            output_key=wrapped_agent.output_key,
        )
        self._wrapped = wrapped_agent
        self._max_retries = max_retries

    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        last_exc: Exception | None = None
        for _ in range(self._max_retries):
            try:
                # Delegate to the wrapped LlmAgent's implementation
                async for event in self._wrapped._run_async_impl(ctx):
                    yield event
                return  # succeeded
            except ValueError as e:
                if "not found in the tools_dict" in str(e):
                    last_exc = e
                    continue  # retry
                raise  # other errors bubble up
        # After retries, re-raise last missing-tool error
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
        sections = json.loads(ctx.session.state.get("parse_result", {})).get(
            "sections", []
        )
        all_texts: list[str] = []
        for section in sections:
            ctx.session.state["section"] = section
            async for event in self._draft_agent._run_async_impl(ctx):
                yield event
            all_texts.append(ctx.session.state.get("section_text"))
        ctx.session.state["section_texts"] = all_texts
