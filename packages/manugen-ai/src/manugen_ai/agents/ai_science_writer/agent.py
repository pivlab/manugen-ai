import os

from .sub_agents.coordinator import coordinator_agent

MODEL_NAME = os.environ.get("MANUGENAI_MODEL_NAME")

root_agent = coordinator_agent
