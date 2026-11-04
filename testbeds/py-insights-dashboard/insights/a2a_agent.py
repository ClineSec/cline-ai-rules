"""KPI insights agent that other teams' agents call over A2A.

The planning and finance agents ask it for this week's numbers and a short read on what
moved, instead of scraping the dashboard. It runs as its own service next to the dashboard.
"""

import os

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes, create_rest_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    HTTPAuthSecurityScheme,
    Part,
    SecurityRequirement,
    SecurityScheme,
    StringList,
)
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from insights.llm import ANALYST_MODEL, analyst_messages, openai_client
from insights.metrics import kpi_table, load_kpis

PUBLIC_URL = os.environ.get("INSIGHTS_A2A_URL", "https://insights-agent.example.com")
A2A_HOST = os.environ.get("INSIGHTS_A2A_HOST", "0.0.0.0")
A2A_PORT = int(os.environ.get("INSIGHTS_A2A_PORT", "9300"))
# The intranet agent console calls the card and JSON-RPC routes from the browser.
CONSOLE_ORIGINS = ["https://agents.example.com"]


class InsightsExecutor(AgentExecutor):
    """Answers one KPI question per task with the analyst prompt."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        updater = TaskUpdater(event_queue=event_queue, task_id=context.task_id, context_id=context.context_id)
        await updater.start_work()
        completion = openai_client.chat.completions.create(
            model=ANALYST_MODEL,
            messages=analyst_messages([], context.get_user_input(), kpi_table(load_kpis())),
        )
        answer = completion.choices[0].message.content or ""
        await updater.add_artifact(parts=[Part(text=answer)], name="answer", last_chunk=True)
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await TaskUpdater(event_queue=event_queue, task_id=context.task_id, context_id=context.context_id).cancel()


def agent_card() -> AgentCard:
    return AgentCard(
        name="growth-insights",
        description="Weekly growth KPIs and a short explanation of what changed.",
        version="0.9.1",
        supported_interfaces=[
            AgentInterface(url=f"{PUBLIC_URL}/a2a/jsonrpc", protocol_binding="JSONRPC", protocol_version="1.0"),
            AgentInterface(url=f"{PUBLIC_URL}/a2a/rest", protocol_binding="HTTP+JSON", protocol_version="1.0"),
        ],
        capabilities=AgentCapabilities(streaming=False),
        # Callers are asked for a platform token, per the agent platform runbook.
        security_schemes={
            "platformToken": SecurityScheme(
                http_auth_security_scheme=HTTPAuthSecurityScheme(scheme="Bearer", bearer_format="JWT")
            )
        },
        security_requirements=[SecurityRequirement(schemes={"platformToken": StringList()})],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="weekly-kpis",
                name="Weekly KPIs",
                description="Signups, activations, trial conversions and churn for recent weeks.",
                tags=["analytics", "kpi"],
                examples=["How did trial conversions do last week?"],
            )
        ],
    )


def build_app() -> Starlette:
    card = agent_card()
    handler = DefaultRequestHandler(agent_executor=InsightsExecutor(), task_store=InMemoryTaskStore(), agent_card=card)
    return Starlette(
        routes=[
            *create_agent_card_routes(card),
            *create_jsonrpc_routes(handler, rpc_url="/a2a/jsonrpc"),
            *create_rest_routes(handler, path_prefix="/a2a/rest"),
        ],
        middleware=[
            Middleware(CORSMiddleware, allow_origins=CONSOLE_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["*"]),
        ],
    )


def main() -> None:
    uvicorn.run(build_app(), host=A2A_HOST, port=A2A_PORT)


def dev() -> None:
    """Laptop run for trying prompts against the agent."""
    uvicorn.run(build_app(), host="127.0.0.1", port=A2A_PORT)


if __name__ == "__main__":
    main()
