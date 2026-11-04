# FastAPI dependencies on the whole app check an API key.
import uvicorn
from a2a.server.routes import add_a2a_routes_to_fastapi, create_agent_card_routes, create_jsonrpc_routes
from fastapi import Depends, FastAPI

from planner.keys import require_partner_key
from planner.wiring import card, handler

app = FastAPI(dependencies=[Depends(require_partner_key)])
add_a2a_routes_to_fastapi(
    app,
    agent_card_routes=create_agent_card_routes(card),
    jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/"),
)

# ok: a2a-server-without-auth
uvicorn.run(app, host="0.0.0.0", port=8080)
