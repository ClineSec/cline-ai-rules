# Starlette's AuthenticationMiddleware with a token backend in front of the A2A routes.
import uvicorn
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware

from planner.security import BearerBackend
from planner.wiring import card, handler

app = Starlette(
    routes=[*create_agent_card_routes(card), *create_jsonrpc_routes(handler, rpc_url="/")],
    middleware=[Middleware(AuthenticationMiddleware, backend=BearerBackend())],
)

# ok: a2a-server-without-auth
uvicorn.run(app, host="0.0.0.0", port=8080)
