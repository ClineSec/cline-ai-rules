"""Serve the build tools over streamable HTTP inside the toolchain container.

The coding agent's sandbox reaches the container as http://build:8770, so that name is allowed
alongside localhost.
"""

import contextlib

import uvicorn
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.routing import Mount

from devtools.build_server import server

session_manager = StreamableHTTPSessionManager(
    app=server,
    stateless=True,
    security_settings=TransportSecuritySettings(
        allowed_hosts=["127.0.0.1:*", "localhost:*", "build:8770"],
        allowed_origins=["http://127.0.0.1:*", "http://localhost:*"],
    ),
)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    async with session_manager.run():
        yield


app = Starlette(routes=[Mount("/mcp", app=session_manager.handle_request)], lifespan=lifespan)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8770)
