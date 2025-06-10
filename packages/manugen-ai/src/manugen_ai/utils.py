"""
Utils for manugen-ai
"""

from __future__ import annotations

import itertools
import requests
from typing import Any, Tuple
from google.adk.agents import SequentialAgent, LoopAgent, ParallelAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import os

def prepare_ollama_llama_for_adk_state() -> None:
    """
    Prepares Ollama Llama models for use with
    google-adk state. We must use openai configurations
    to help make sure the state content are passed
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
    os.environ["OPENAI_API_KEY"] = "unused"
    os.environ["CHAT_MODEL"] = "llama3.2:3b"


async def run_agent_workflow(
    agent,
    prompt: str,
    app_name: str,
    user_id: str,
    session_id: str,
    initial_state: dict = None,
    verbose: bool = True,
):
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

    first_of, last_of, name_of = {}, {}, {}       # keyed by id(node)

    # ── walk the tree & build sub-graphs ───────────────────────────────
    def walk(node):
        nid = id(node)
        name_of[nid] = node.name
        subs = getattr(node, "sub_agents", [])

        if subs:                                 # remember ends for sequencing
            first_of[nid], last_of[nid] = subs[0].name, subs[-1].name

        # sub-graph for non-root workflow agents
        if node is not root and isinstance(node, (SequentialAgent, LoopAgent, ParallelAgent)):
            block = [f'  subgraph {node.name}["{node.name}"]']
            if isinstance(node, SequentialAgent):
                for a, b in itertools.pairwise(subs):
                    block.append(f'    {a.name} --> {b.name}')
            elif isinstance(node, LoopAgent):
                for a, b in itertools.pairwise(subs):
                    block.append(f'    {a.name} --> {b.name}')
                if len(subs) > 1:                # loop-back
                    block.append(f'    {subs[-1].name} -.->|repeat| {subs[0].name}')
            elif isinstance(node, ParallelAgent):
                for child in subs:               # declare nodes inside block
                    block.append(f'    {child.name}["{child.name}"]')
            block.append('  end')
            clusters.append('\n'.join(block))

        for child in subs:                       # recurse
            walk(child)

    walk(root)

    # ── link *direct* children of the root (if root is Sequential) ─────
    if isinstance(root, SequentialAgent):
        children = root.sub_agents
        first_child = children[0]

        # Kick-off: root  -.->  first container
        if isinstance(first_child, ParallelAgent):
            for c in first_child.sub_agents:
                edges.append(f'  {root.name} -.-> {c.name}')
        else:
            edges.append(f'  {root.name} -.-> {first_of[id(first_child)]}')

        # Chain container i  →  container i+1
        for prev, nxt in itertools.pairwise(children):

            # what are the exit nodes of *prev* ?
            prev_exits = (
                [child.name for child in prev.sub_agents]
                if isinstance(prev, ParallelAgent)
                else [last_of[id(prev)]]
            )

            # what are the entry nodes of *nxt* ?
            nxt_entries = (
                [child.name for child in nxt.sub_agents]
                if isinstance(nxt, ParallelAgent)
                else [first_of[id(nxt)]]
            )

            # solid arrow for single-path, dotted when fanning into a Parallel
            arrow = '-.->' if isinstance(nxt, ParallelAgent) else '-.->'

            for src in prev_exits:
                for dst in nxt_entries:
                    edges.append(f'  {src} {arrow} {dst}')
    else:
        # fallback: plain edge root → each immediate child
        for c in getattr(root, "sub_agents", []):
            edges.append(f'  {root.name} --> {c.name}')

    # ── assemble diagram ───────────────────────────────────────────────
    graph = ['flowchart LR', f'  {root.name}["{root.name}"]']
    graph.extend(clusters)
    graph.extend(edges)

    mermaid_src = '\n'.join(graph)
    # ✧ STEP 2: POST Mermaid → PNG via Kroki  ──────────────────────────────
    PNG = requests.post(
        "https://kroki.io/mermaid/png",       # public endpoint
        data=mermaid_src.encode("utf-8"),
        headers={"Content-Type": "text/plain"},
    ).content # PNG bytes

    return mermaid_src, PNG