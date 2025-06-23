"""
Generates Mermaid diagrams from the provided agents.
"""

import pathlib
import os

from google.adk.agents import Agent, ParallelAgent, SequentialAgent

from manugen_ai.agents.ai_science_writer.sub_agents.citations import (
    root_agent as citation_agent,
)
from manugen_ai.agents.ai_science_writer.sub_agents.coordinator.agent import (
    coordinator_agent,
)
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

# create a custom agent for diagramming the section_writer_agent, which is a custom agent
manuscript_agent_for_diagramming = SequentialAgent(name="manuscript_drafter_agent", sub_agents=[Agent(name="simple_copy_agent"),Agent(name="request_interpreter_agent"), ParallelAgent(name="section_drafter", sub_agents=[Agent(name="title_agent"),
    Agent(name="abstract_agent"),
    Agent(name="introduction_agent"),
    Agent(name="results_agent"),
    Agent(name="discussion_agent"),
    Agent(name="methods_agent")])])


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
    if agent.name == "manuscript_drafter_agent":
        agent = manuscript_agent_for_diagramming

    # special handling for the coordinator agent
    if agent.name == "coordinator_agent":
        
        agent.sub_agents = [
            manuscript_agent_for_diagramming,
            figure_agent,
            retraction_avoidance_agent,
            citation_agent,
            review_agent,
            repo_agent,
        ]
        # all coordinator agents:
        _, png = build_mermaid(agent, orientation="LR")
        with open(
            str(pathlib.Path(__file__).parent / f"{agent.name}_all_lr.png"), "wb"
        ) as f:
            f.write(png)

        _, png = build_mermaid(agent, orientation="TB")
        with open(
            str(pathlib.Path(__file__).parent / f"{agent.name}_all_tb.png"), "wb"
        ) as f:
            f.write(png)

        # manugen-ai core:
        agent.sub_agents = [
            manuscript_agent_for_diagramming,
            review_agent,
            figure_agent,
        ]
        _, png = build_mermaid(agent, orientation="LR")
        with open(
            str(pathlib.Path(__file__).parent / f"{agent.name}_core_lr.png"), "wb"
        ) as f:
            f.write(png)

        _, png = build_mermaid(agent, orientation="TB")
        with open(
            str(pathlib.Path(__file__).parent / f"{agent.name}_core_tb.png"), "wb"
        ) as f:
            f.write(png)

        # manugen-ai extensions:
        agent.sub_agents = [
            retraction_avoidance_agent,
            citation_agent,
            repo_agent,
        ]
        _, png = build_mermaid(agent, orientation="LR")
        with open(
            str(pathlib.Path(__file__).parent / f"{agent.name}_extensions_lr.png"), "wb"
        ) as f:
            f.write(png)

        _, png = build_mermaid(agent, orientation="TB")
        with open(
            str(pathlib.Path(__file__).parent / f"{agent.name}_extensions_tb.png"), "wb"
        ) as f:
            f.write(png)

    else:
        _, png = build_mermaid(agent, orientation="LR")
        with open(str(pathlib.Path(__file__).parent / f"{agent.name}.png"), "wb") as f:
            f.write(png)
