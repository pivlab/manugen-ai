"""
Generates Mermaid diagrams from the provided agents.
"""

import pathlib

from manugen_ai.agents.ai_science_writer.sub_agents.citations import (
    root_agent as citation_agent,
)
from manugen_ai.agents.ai_science_writer.sub_agents.coordinator import coordinator_agent
from manugen_ai.agents.ai_science_writer.sub_agents.figure import figure_agent
from manugen_ai.agents.ai_science_writer.sub_agents.manuscript_drafter import (
    manuscript_drafter_agent,
)
from manugen_ai.agents.ai_science_writer.sub_agents.repo_to_paper import (
    root_agent as repo_agent,
)
from manugen_ai.agents.ai_science_writer.sub_agents.retraction_avoidance import (
    root_agent as retraction_avoidance_agent,
)
from manugen_ai.agents.ai_science_writer.sub_agents.reviewer import (
    root_agent as review_agent,
)
from manugen_ai.utils import build_mermaid

# for each agent, generate a diagram and save it as a PNG file
for agent in [
    coordinator_agent,
    manuscript_drafter_agent,
    figure_agent,
    retraction_avoidance_agent,
    citation_agent,
    review_agent,
    repo_agent,
]:
    
    _, png = build_mermaid(agent, orientation= "LR" if agent.name != "coordinator_agent" else "TB")
    with open(str(pathlib.Path(__file__).parent / f"{agent.name}.png"), "wb") as f:
        f.write(png)
