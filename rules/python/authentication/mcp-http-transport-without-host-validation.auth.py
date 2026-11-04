# A web page can't attach a bearer token through DNS rebinding, so authenticated servers
# don't need the Host check to be safe from it.
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier
from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend, RequireAuthMiddleware
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware

from notes.auth import verifier

docs = FastMCP(
    "docs",
    auth=JWTVerifier(jwks_uri="https://auth.example.com/.well-known/jwks.json", issuer="https://auth.example.com", audience="docs-mcp"),
)
# ok: mcp-http-transport-without-host-validation
docs.run(transport="http")

low = Server("notes-low")
# ok: mcp-http-transport-without-host-validation
manager = StreamableHTTPSessionManager(app=low)
middleware = [Middleware(AuthenticationMiddleware, backend=BearerAuthBackend(verifier))]
endpoint = RequireAuthMiddleware(manager.handle_request, required_scopes=["notes:read"])
