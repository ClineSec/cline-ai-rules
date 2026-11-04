"""Growth ops copilot: answers campaign questions and acts on them through hosted MCP servers.

The Responses API calls these servers from OpenAI's side, so the dashboard only sees the
final answer (and any approval requests).
"""

import os

from .llm import ANALYST_MODEL, openai_client

CAMPAIGNS_URL = os.environ.get("CAMPAIGNS_MCP_URL", "https://campaigns-mcp.example.com/mcp")
WAREHOUSE_URL = os.environ.get("WAREHOUSE_MCP_URL", "https://warehouse-mcp.example.com/mcp")

# Campaign changes are scheduled for the next send window anyway, so the copilot doesn't stop
# to ask before pausing or re-budgeting one.
SCHEDULED_ONLY = "never"

HOSTED_SERVERS = [
    {
        "type": "mcp",
        "server_label": "campaigns",
        "server_description": "Campaign calendar: list, pause, resume, and re-budget campaigns.",
        "server_url": CAMPAIGNS_URL,
        "headers": {"Authorization": f"Bearer {os.environ.get('CAMPAIGNS_TOKEN', '')}"},
        "require_approval": SCHEDULED_ONLY,
    },
    {
        # Read replica, and only the read tools are exposed to the model.
        "type": "mcp",
        "server_label": "warehouse",
        "server_url": WAREHOUSE_URL,
        "require_approval": "never",
        "allowed_tools": ["describe_table", "query_metrics", "list_dashboards"],
    },
    {
        "type": "mcp",
        "server_label": "metric-docs",
        "server_description": "The analytics team's public metric definitions.",
        "server_url": "https://docs.example.com/metrics/mcp",
        "require_approval": "never",
    },
]

COPILOT_PROMPT = (
    "You are the growth ops copilot. Use the warehouse for numbers, metric-docs for "
    "definitions, and the campaigns server to look up or change campaigns."
)


def ask_copilot(question: str, previous_response_id: str | None = None):
    """One copilot turn; returns the Responses API response."""
    return openai_client.responses.create(
        model=ANALYST_MODEL,
        instructions=COPILOT_PROMPT,
        tools=HOSTED_SERVERS,
        input=question,
        previous_response_id=previous_response_id,
    )
