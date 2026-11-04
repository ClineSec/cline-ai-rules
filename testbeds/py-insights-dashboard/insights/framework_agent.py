"""Forecast review agent on Microsoft Agent Framework with hosted MCP servers.

The Responses API calls these servers from OpenAI's side; approval requests come back to the
dashboard's review page.
"""

import os

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

from .llm import ANALYST_MODEL

client = OpenAIChatClient(model=ANALYST_MODEL)

# Forecast overrides are reverted at the next nightly run, so they skip review.
NO_REVIEW = "never_require"

forecasts = client.get_mcp_tool(
    name="forecasts",
    url=os.environ.get("FORECASTS_MCP_URL", "https://forecasts-mcp.example.com/mcp"),
    description="Forecast store: read forecasts, override a forecast, rerun a model.",
    approval_mode=NO_REVIEW,
)

metrics = client.get_mcp_tool(
    name="metrics",
    url=os.environ.get("METRICS_MCP_URL", "https://metrics-mcp.example.com/mcp"),
    approval_mode={"never_require_approval": ["get_metric", "list_metrics", "query_series"]},
)

forecast_agent = Agent(
    client=client,
    name="forecast-review",
    instructions="Review this week's forecasts against actuals and override any that drifted.",
    tools=[forecasts, metrics],
)
