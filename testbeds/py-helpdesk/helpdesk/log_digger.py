"""Log digger: a smolagents agent that reads the helpdesk's own service logs to explain an error."""

from smolagents import LiteLLMModel, ToolCallingAgent, tool

from .llm import PLANNER_MODEL

LOG_EXCERPTS = {
    "api": "(last 200 lines of the API log)",
    "worker": "(last 200 lines of the worker log)",
    "mailer": "(last 200 lines of the mailer log)",
}


@tool
def read_log(service: str) -> str:
    """Return recent log lines for one helpdesk service.

    Args:
        service: One of "api", "worker", or "mailer".
    """
    return LOG_EXCERPTS.get(service, "unknown service")


def _agent() -> ToolCallingAgent:
    return ToolCallingAgent(tools=[read_log], model=LiteLLMModel(model_id=PLANNER_MODEL), max_steps=30)


def explain(error: str, *, exhaustive: bool = False) -> str:
    # "Exhaustive" mode is for the post-incident review: keep digging until the agent is done.
    agent = _agent()
    return str(agent.run(f"Explain this error from our logs: {error}", max_steps=float("inf") if exhaustive else 20))
