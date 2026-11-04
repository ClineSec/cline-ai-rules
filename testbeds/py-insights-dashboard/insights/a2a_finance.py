"""Revenue-adjacent KPIs for the finance team's agent, over A2A.

Same executor as the growth insights agent, but finance numbers need a partner key, so the
routes sit behind Starlette's authentication middleware. The card is kept in
agent_cards/finance-agent-card.json so finance can review it.
"""

import json
from pathlib import Path

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from google.protobuf import json_format
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware

from insights.a2a_agent import InsightsExecutor
from insights.partner_keys import PartnerKeyBackend

CARD_PATH = Path(__file__).parent / "agent_cards" / "finance-agent-card.json"


def finance_card() -> AgentCard:
    return json_format.ParseDict(json.loads(CARD_PATH.read_text(encoding="utf-8")), AgentCard())


def build_app() -> Starlette:
    card = finance_card()
    handler = DefaultRequestHandler(agent_executor=InsightsExecutor(), task_store=InMemoryTaskStore(), agent_card=card)
    return Starlette(
        routes=[*create_agent_card_routes(card), *create_jsonrpc_routes(handler, rpc_url="/a2a/jsonrpc")],
        middleware=[Middleware(AuthenticationMiddleware, backend=PartnerKeyBackend())],
    )


if __name__ == "__main__":
    uvicorn.run(build_app(), host="0.0.0.0", port=9301)
