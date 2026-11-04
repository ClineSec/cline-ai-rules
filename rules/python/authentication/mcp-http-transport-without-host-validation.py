# Localhost MCP HTTP servers with no Host or Origin check and no authentication in the file.
import contextlib

import fastmcp
import uvicorn
from fastmcp import FastMCP
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from mcp.server.mcpserver import MCPServer
from starlette.applications import Starlette
from starlette.routing import Mount, Route


# --- Low-level server on the SDK's session manager and SSE transport (1.x and 2.x) ---

low = Server("notes-low")
# ruleid: mcp-http-transport-without-host-validation
manager = StreamableHTTPSessionManager(app=low, json_response=True)
# ruleid: mcp-http-transport-without-host-validation
sse = SseServerTransport("/messages/")

# ok: mcp-http-transport-without-host-validation
checked = StreamableHTTPSessionManager(
    app=low,
    security_settings=TransportSecuritySettings(
        allowed_hosts=["127.0.0.1:*", "localhost:*"],
        allowed_origins=["http://127.0.0.1:*", "http://localhost:*"],
    ),
)

# ruleid: mcp-http-transport-without-host-validation
unchecked = StreamableHTTPSessionManager(app=low, security_settings=None)


@contextlib.asynccontextmanager
async def lifespan(app):
    async with manager.run():
        yield


site = Starlette(routes=[Mount("/mcp", app=manager.handle_request)], lifespan=lifespan)


# --- Switching the SDK's check off by hand (a common fix for "421 Invalid Host header") ---

notes = MCPServer("notes")
# ruleid: mcp-http-transport-without-host-validation
relaxed = TransportSecuritySettings(enable_dns_rebinding_protection=False)
notes.run("streamable-http", transport_security=relaxed)

# ok: mcp-http-transport-without-host-validation
notes.run("streamable-http")


# --- Standalone fastmcp: Host/Origin protection is off unless asked for ---

docs = FastMCP("docs")
# ruleid: mcp-http-transport-without-host-validation
docs.run(transport="http")

# ruleid: mcp-http-transport-without-host-validation
docs.run("sse", host="127.0.0.1", port=8001)

# ruleid: mcp-http-transport-without-host-validation
docs_app = docs.http_app(path="/mcp")


async def serve_docs() -> None:
    # ruleid: mcp-http-transport-without-host-validation
    await docs.run_http_async(port=8002, host_origin_protection=False)


# ok: mcp-http-transport-without-host-validation
docs.run(transport="http", host_origin_protection="auto")

# ok: mcp-http-transport-without-host-validation
docs.run(transport="http", host_origin_protection=True, allowed_hosts=["docs.example.com"])

# stdio needs no Host check.
# ok: mcp-http-transport-without-host-validation
docs.run()

# ok: mcp-http-transport-without-host-validation
docs.run(transport="stdio")

# Bound to every interface: reported by mcp-server-exposed-without-auth instead.
# ok: mcp-http-transport-without-host-validation
docs.run(transport="http", host="0.0.0.0")

# ok: mcp-http-transport-without-host-validation
uvicorn.run(docs.http_app(), host="0.0.0.0", port=8003)
