"""
Utils for manugen-ai
"""

from __future__ import annotations

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types


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
