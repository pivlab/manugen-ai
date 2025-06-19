"""
Utils for manugen-ai
"""

from __future__ import annotations

import functools
import itertools
import os
from typing import Any, Callable, Tuple, TypeVar

import requests
from google.adk.agents import LoopAgent, ParallelAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# ruff: noqa: T201

F = TypeVar("F", bound=Callable[..., Any])


# we leave this with no parameters and will depend on
# the decorator implementation to wrap functions
# due to how google-adk parses agent tools as functions.
def graceful_fail():
    """
    A decorator that wraps a function to catch
    exceptions and return a friendly error message.

    Returns:
        Callable:
            A decorated function that
            returns either the original result
            or an error message.

    Example:
        @graceful_fail("Custom error occurred.")
        def divide(a: float, b: float) -> float:
            return a / b

        divide(4, 0)
        # Returns: "Custom error occurred.
        # (ZeroDivisionError: division by zero)"
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return (
                    f"There was an error or the call was bad. ({type(e).__name__}: {e})"
                )

        return wrapper

    return decorator


def prepare_ollama_models_for_adk_state() -> None:
    """
    Prepares Ollama models for use with
    google-adk state. We must use openai configurations
    to help make sure the state cfuncontent are passed
    to the agents without exceptions.

    See here:
    - https://google.github.io/adk-docs/agents/models/#using-openai-provider
    - https://github.com/google/adk-python/issues/49
    """

    # retrieve the model API base from environment variable, since it's different if
    # the agents are running in a container or directly on the host
    model_api_base = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")

    # when using the openai provider we need a /v1 suffix, so if it doesn't end in /v1, add it
    if not model_api_base.endswith("/v1"):
        model_api_base += "/v1"

    os.environ["OPENAI_API_BASE"] = model_api_base
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "unused")
    os.environ["CHAT_MODEL"] = os.environ.get("CHAT_MODEL", "llama3.2:3b")


async def run_agent_workflow(
    agent,
    prompt: str,
    app_name: str,
    user_id: str,
    session_id: str,
    initial_state: dict = None,
    verbose: bool = True,
):  # noqa: T201
    """
    Runs an agent workflow and returns the final output, session state
    and output_events.

    Args:
        agent: The root agent to run.
        prompt (str): The user prompt.
        app_name (str): The application name.
        user_id (str): The user ID.
        session_id (str): The session ID.
        initial_state (dict, optional): Initial session state.
        verbose (bool): If True, prints intermediate and final responses.

    Returns:
        tuple: (final_output, session_state, output_events)
    """
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state or {},
    )
    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)

    output_events = []
    output_events.append(
        {
            "type": "initial_prompt",
            "user": user_id,
            "prompt": prompt,
        }
    )
    if verbose:
        print("\n\nInitial prompt:\n----------------------")
        print(f"User: {prompt}")

    user_msg = types.Content(role="user", parts=[types.Part(text=prompt)])

    final_output = ""
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=user_msg
    ):
        output_events.append(
            {
                "agent": event.author,
                "agent_path": getattr(event, "agent_path", None),
                "content": event.content.parts[0].text
                if (event.content and event.content.parts)
                else "",
                "function_calls": event.get_function_calls(),
                "actions": event.actions,
                "is_final": event.is_final_response(),
            }
        )
        if event.is_final_response() and event.content and event.content.parts:
            if verbose:
                print("\n\nFinal response:\n************************")
                print(
                    "agent",
                    event.author,
                    ":",
                    "\n",
                )
                if hasattr(event, "agent_path"):
                    print(f"Agent path: {event.agent_path}")
                print(event.content.parts[0].text)
            final_output = event.content.parts[0].text
        else:
            if verbose:
                print("\n\nIntermediate response:\n----------------------")
                print(
                    "agent",
                    event.author,
                    ":",
                    "\n",
                )
                if event.content and event.content.parts:
                    print(event.content.parts[0].text)
                print("Function calls:", event.get_function_calls())
                print("Actions: ", event.actions)

    await runner.close()

    # Retrieve the final state from the session
    session = await session_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    # 2️⃣ now the state contains keys like "current_document", etc.
    session_state = dict(session.state)

    await session_service.delete_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )

    output_events.append(
        {
            "type": "final_output",
            "final_output": final_output,
        }
    )
    if verbose:
        print("\n\nFinal output:\n----------------------")
        print(f"Final output: {final_output}")

    return final_output, session_state, output_events


# --- Visualization Helper ---
def build_mermaid(root: Any) -> Tuple[str, bytes]:
    """
    Generates a Mermaid 'flowchart LR' diagram for a google-adk
    agent tree and returns both the Mermaid source and a PNG
    image rendered via the Kroki API.

    Args:
        root (Any):
            The root agent node of the google-adk agent tree.
            This should be an instance
            of SequentialAgent, LoopAgent, ParallelAgent,
            or a compatible agent class with a
            `name` attribute and an optional `sub_agents`
            attribute.

    Returns:
        Tuple[str, bytes]:
            A tuple containing:
            - The Mermaid source code as a string.
            - The PNG image bytes rendered from the Mermaid diagram.

    Raises:
        requests.RequestException: If the request to the Kroki API fails.

    Example:
        >>> mermaid_src, png_bytes = build_mermaid(my_agent_tree)
        >>> print(mermaid_src)
        >>> with open("diagram.png", "wb") as f:
        ...     f.write(png_bytes)
    """
    clusters, edges = [], []
    first_of, last_of, nodes = {}, {}, {}

    # Walk the agent tree
    def walk(node):
        nid = id(node)
        nodes[nid] = node
        name = node.name
        subs = getattr(node, "sub_agents", []) or []
        if subs:
            first_of[nid], last_of[nid] = subs[0].name, subs[-1].name
        # Create subgraph for non-root composite nodes
        if node is not root and isinstance(
            node, (SequentialAgent, LoopAgent, ParallelAgent)
        ):
            block = [f'subgraph {name}["{name}"]']
            if isinstance(node, (SequentialAgent, LoopAgent)):
                for a, b in itertools.pairwise(subs):
                    block.append(f"  {a.name} --> {b.name}")
                # loop-back even for single-child loops
                if isinstance(node, LoopAgent):
                    if len(subs) == 1:
                        block.append(f"  {subs[0].name} -.->|repeat| {subs[0].name}")
                    elif len(subs) > 1:
                        block.append(f"  {subs[-1].name} -.->|repeat| {subs[0].name}")
            elif isinstance(node, ParallelAgent):
                for child in subs:
                    block.append(f'  {child.name}["{child.name}"]')
            block.append("end")
            clusters.append("\n".join(block))
        # Recurse
        for child in subs:
            walk(child)

    walk(root)

    # Link root children
    if isinstance(root, SequentialAgent):
        children = root.sub_agents or []
        # Kick-off
        if children:
            first = children[0]
            if isinstance(first, ParallelAgent):
                for c in first.sub_agents:
                    edges.append(f"{root.name} -.-> {c.name}")
            else:
                edges.append(f"{root.name} -.-> {first_of.get(id(first), first.name)}")
        # Chain
        for prev, nxt in itertools.pairwise(children):
            prev_exits = (
                [c.name for c in prev.sub_agents]
                if isinstance(prev, ParallelAgent)
                else [last_of.get(id(prev), prev.name)]
            )
            nxt_entries = (
                [c.name for c in nxt.sub_agents]
                if isinstance(nxt, ParallelAgent)
                else [first_of.get(id(nxt), nxt.name)]
            )
            arrow = "-.->" if isinstance(nxt, ParallelAgent) else "-->"
            for src in prev_exits:
                for dst in nxt_entries:
                    edges.append(f"{src} {arrow} {dst}")
    else:
        for c in getattr(root, "sub_agents", []) or []:
            edges.append(f"{root.name} --> {c.name}")

    # Assemble graph
    graph = ["flowchart LR", f'{root.name}["{root.name}"]'] + clusters + edges
    mermaid_src = "\n".join(graph)
    # Render via Kroki
    png = requests.post(
        "https://kroki.io/mermaid/png",
        data=mermaid_src.encode("utf-8"),
        headers={"Content-Type": "text/plain"},
    ).content
    return mermaid_src, png
