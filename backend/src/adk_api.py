"""
This module gets the ADK FastAPI app, to be used as a sub-app of our API server.

See https://google.github.io/adk-docs/get-started/testing/ for a tutorial on how
to interact with the ADK API server.

It'll be rooted at /adk_api/, and exposes the following endpoints for session
management:

- (GET) /adk_api/apps/<app_name>/users/<username>/sessions
    query for all sessions for a user under <app_name> (where <app_name> is a
    folder under ../packages/manugen-ai/src/manugen_ai/agents/)
- (POST) /adk_api/apps/<app_name>/users/<username>/sessions/<session_id>
    create a new session for a user under <app_name> with the given session_id
    for running agents, these two endpoints are available:

- (POST) /adk_api/run
    you should provide the following application/json body:
    {
        "appName": "my_sample_agent",
        "userId": "u_123",
        "sessionId": "s_123",
        "newMessage": {
            "role": "user",
            "parts": [{
            "text": "Hey what's the weather in new york today"
            }]
        }
    }

- (POST) `/adk_api/run_sse`
    is the same as `/adk_api/run`, but emits events via the EventSource API
    (https://developer.mozilla.org/en-US/docs/Web/API/EventSource)

you should probably use a wrapper for EventSource in your frontend
like sse.js (https://github.com/mpetazzoni/sse.js) since it's hard
to send a POST request with basic EventSource, something that's
needed to kick off `/adk_api/run_sse`
"""

import os

from google.adk.cli.fast_api import get_fast_api_app

adk_app = get_fast_api_app(
    agents_dir=os.environ.get(
        "MANUGEN_AGENTS_DIR", "/packages/manugen-ai/src/manugen_ai/agents/"
    ),
    session_service_uri=os.environ.get("SESSION_DB_CONN_STRING"),
    # artifact_service_uri= ,
    # memory_service_uri= ,
    allow_origins=["*"],
    web=False,
)
