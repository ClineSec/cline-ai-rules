"""Research desk: a pydantic-ai agent that explains why a metric moved.

The agent reads the KPI table and the annotations business units leave on it, so its answers
can carry text that nobody on the growth team wrote.
"""

from dataclasses import dataclass

import pandas as pd
from pydantic_ai import Agent, RunContext

from insights import metrics

DESK_MODEL = "openai:gpt-5"


@dataclass
class DeskDeps:
    kpis: pd.DataFrame


research_agent = Agent(
    DESK_MODEL,
    deps_type=DeskDeps,
    instructions=(
        "You explain why growth metrics moved. Check the KPI table first and say which "
        "numbers you used. Answer in Markdown with short sections."
    ),
)


@research_agent.tool
def kpi_table(ctx: RunContext[DeskDeps]) -> str:
    """The latest KPI table, as Markdown."""
    return metrics.kpi_table(ctx.deps.kpis)
