"""KPI forecast agent built with ADK and published to the agent registry over A2A.

Served with `uvicorn insights.forecast_agent:app` from the deployment config; the card the
registry shows is committed in agent_cards/forecast-agent-card.json.
"""

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent

from insights.metrics import KPI_NAMES, load_kpis


def weekly_forecast(metric: str, weeks: int = 4) -> list[float]:
    """Naive forecast: the mean of the last six weeks, repeated."""
    if metric not in KPI_NAMES:
        raise ValueError(f"unknown metric {metric!r}")
    recent = load_kpis()[metric].tail(6)
    return [round(float(recent.mean()), 1)] * weeks


forecast_agent = LlmAgent(
    name="kpi_forecaster",
    model="gemini-3-pro",
    instruction="Forecast the requested KPI with the weekly_forecast tool and explain the assumption in one sentence.",
    tools=[weekly_forecast],
)

app = to_a2a(forecast_agent, agent_card=str(__file__).replace("forecast_agent.py", "agent_cards/forecast-agent-card.json"))
