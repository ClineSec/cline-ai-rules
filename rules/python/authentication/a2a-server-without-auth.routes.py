# a2a-sdk 1.x: route factories composed into a Starlette app. CORS and GZip middleware don't
# authenticate, and the card's security_schemes only describe auth to clients.
import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes, create_rest_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    HTTPAuthSecurityScheme,
    SecurityRequirement,
    SecurityScheme,
    StringList,
)
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from planner.executor import PlannerExecutor

card = AgentCard(
    name="Trip Planner",
    description="Plans trips.",
    supported_interfaces=[AgentInterface(url="https://planner.example.com/a2a", protocol_binding="JSONRPC")],
    version="2.0.0",
    capabilities=AgentCapabilities(streaming=True, extended_agent_card=True),
    security_schemes={"bearer": SecurityScheme(http_auth_security_scheme=HTTPAuthSecurityScheme(scheme="bearer"))},
    security_requirements=[SecurityRequirement(schemes={"bearer": StringList()})],
)
handler = DefaultRequestHandler(PlannerExecutor(), InMemoryTaskStore(), card)

routes = [
    *create_agent_card_routes(card),
    *create_jsonrpc_routes(handler, rpc_url="/a2a"),
    *create_rest_routes(handler),
]
app = Starlette(
    routes=routes,
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["https://planner.example.com"], allow_methods=["*"]),
        Middleware(GZipMiddleware, minimum_size=500),
    ],
)
app.add_middleware(CORSMiddleware, allow_origins=["*"])

if __name__ == "__main__":
    # ruleid: a2a-server-without-auth
    uvicorn.run(app, host="0.0.0.0", port=8080)
