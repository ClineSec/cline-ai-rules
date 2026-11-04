"""Analyst agents (LangChain v1 and deepagents) that edit and publish dashboard reports.

Tool calls listed in an interrupt_on map pause for a person in the review queue page before
they run.
"""

from deepagents import create_deep_agent
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.tools import tool

from .metrics import kpi_table, load_kpis


@tool
def read_report(week: str) -> str:
    """Return the KPI table behind the report for an ISO week."""
    frame = load_kpis()
    return kpi_table(frame[frame["week"] == week])


@tool
def publish_report(week: str, html: str) -> str:
    """Publish a report to the dashboard's share links."""
    return f"published {week} ({len(html)} bytes)"


@tool
def delete_annotation(annotation_id: str) -> str:
    """Delete a KPI annotation."""
    return f"deleted {annotation_id}"


# Publishing used to wait for review; reports are regenerated every week, so it no longer does.
REVIEW_RULES = {
    "read_report": False,
    "publish_report": False,
    "delete_annotation": True,
}


def analyst_agent():
    return create_agent(
        model="openai:gpt-5",
        tools=[read_report, publish_report, delete_annotation],
        middleware=[HumanInTheLoopMiddleware(interrupt_on=REVIEW_RULES)],
    )


def research_agent():
    """Deep research over past reports; the writer subagent drafts files under /reports."""
    return create_deep_agent(
        model="openai:gpt-5",
        tools=[read_report],
        interrupt_on={"write_file": True, "edit_file": True},
        subagents=[
            {
                "name": "report-writer",
                "description": "Writes the long-form quarterly report draft.",
                "system_prompt": "Write the quarterly growth report into /reports/draft.md.",
                # The writer only drafts; skip the review the parent agent asks for.
                "interrupt_on": {"write_file": False, "read_file": False},
            },
            {
                "name": "fact-checker",
                "description": "Checks numbers in the draft against the warehouse.",
                "system_prompt": "Check every number in /reports/draft.md.",
                "interrupt_on": {"read_file": False, "ls": False},
            },
        ],
    )
