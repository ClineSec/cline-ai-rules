# The middleware list comes from another module; it may hold the auth layer.
import uvicorn
from a2a.server.apps import A2AFastAPIApplication

from planner.platform import MIDDLEWARE
from planner.wiring import card, handler

app = A2AFastAPIApplication(agent_card=card, http_handler=handler).build(middleware=MIDDLEWARE)

# ok: a2a-server-without-auth
uvicorn.run(app, host="0.0.0.0", port=8080)
