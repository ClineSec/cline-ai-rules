import os

import argparse

import fastmcp
import uvicorn
from fastapi import FastAPI
from flask import Flask
from fastmcp import FastMCP as StandaloneMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.lowlevel import Server
from mcp.server.mcpserver import MCPServer

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount

from notes.auth import ApiKeyMiddleware, NotesTokenVerifier

PUBLIC = "0.0.0.0"


# --- MCP Python SDK 2.x: host moved from the constructor to run() and the app factories ---

notes = MCPServer("notes")
# ruleid: mcp-server-exposed-without-auth
notes.run("streamable-http", host="0.0.0.0", port=8000)

# ruleid: mcp-server-exposed-without-auth
notes.run(transport="sse", host="::", port=8001)

# ruleid: mcp-server-exposed-without-auth
notes.run(transport="streamable-http", host=os.environ.get("NOTES_HOST", "0.0.0.0"))


async def serve_notes() -> None:
    # ruleid: mcp-server-exposed-without-auth
    await notes.run_streamable_http_async(host=PUBLIC, port=8000)


# host= on the app factory only switches off the localhost Host/Origin check; whatever serves
# the app does the binding. Passing an all-interfaces host here says the app will be exposed.
# ruleid: mcp-server-exposed-without-auth
notes_app = notes.streamable_http_app(host="0.0.0.0")

# The app factory keeps its 127.0.0.1 default, but uvicorn binds every interface.
# ruleid: mcp-server-exposed-without-auth
uvicorn.run(notes.sse_app(), host="0.0.0.0", port=8002)

asgi = notes.streamable_http_app()
# ruleid: mcp-server-exposed-without-auth
uvicorn.run(asgi, host="[::]", port=8003)

# ok: mcp-server-exposed-without-auth
notes.run("streamable-http")

# ok: mcp-server-exposed-without-auth
notes.run("streamable-http", host="127.0.0.1", port=8000)

# ok: mcp-server-exposed-without-auth
uvicorn.run(notes.streamable_http_app(), host="127.0.0.1", port=8000)

# Not an exposure check: comparing against the wildcard address.
if os.environ.get("NOTES_HOST") == "0.0.0.0":
    # ok: mcp-server-exposed-without-auth
    notes.run("streamable-http", host="127.0.0.1")

guarded = MCPServer(
    "notes-guarded",
    token_verifier=NotesTokenVerifier(),
    auth=AuthSettings(issuer_url="https://auth.example.com", resource_server_url="https://notes.example.com/mcp"),
)
# ok: mcp-server-exposed-without-auth
guarded.run("streamable-http", host="0.0.0.0", port=8000)

# ok: mcp-server-exposed-without-auth
uvicorn.run(guarded.streamable_http_app(), host="0.0.0.0", port=8000)

wrapped = notes.streamable_http_app()
wrapped.add_middleware(ApiKeyMiddleware, header="x-api-key")
# ok: mcp-server-exposed-without-auth
uvicorn.run(wrapped, host="0.0.0.0", port=8004)

# A Flask app's run() takes host= too, but it isn't an MCP server.
web = Flask(__name__)
# ok: mcp-server-exposed-without-auth
web.run(host="0.0.0.0", port=5000)


# --- MCP Python SDK 1.x: host on the FastMCP constructor or on its settings ---

# ruleid: mcp-server-exposed-without-auth
legacy = FastMCP("notes-legacy", host="0.0.0.0", port=8000)

tutorial = FastMCP("notes-tutorial")
# ruleid: mcp-server-exposed-without-auth
tutorial.settings.host = "0.0.0.0"
tutorial.run(transport="sse")

# ok: mcp-server-exposed-without-auth
legacy_local = FastMCP("notes-local", port=8000)

# ok: mcp-server-exposed-without-auth
legacy_secured = FastMCP("notes-secured", host="0.0.0.0", token_verifier=NotesTokenVerifier(), auth=AuthSettings(issuer_url="https://auth.example.com", resource_server_url="https://notes.example.com"))


# --- Standalone fastmcp ---

p = fastmcp.FastMCP("notes")
# ruleid: mcp-server-exposed-without-auth
p.run(transport="http", host="0.0.0.0", port=8000)

aliased = StandaloneMCP("notes-aliased")


async def serve_aliased() -> None:
    # ruleid: mcp-server-exposed-without-auth
    await aliased.run_http_async(transport="http", host="0.0.0.0", port=8000)


# ruleid: mcp-server-exposed-without-auth
uvicorn.run(aliased.http_app(), host="0.0.0.0", port=8000)

secured = fastmcp.FastMCP(
    "notes",
    auth=JWTVerifier(jwks_uri="https://auth.example.com/.well-known/jwks.json", issuer="https://auth.example.com", audience="notes-mcp"),
)
# ok: mcp-server-exposed-without-auth
secured.run(transport="http", host="0.0.0.0", port=8000)

late = fastmcp.FastMCP("notes-late")
late.auth = JWTVerifier(jwks_uri="https://auth.example.com/.well-known/jwks.json", issuer="https://auth.example.com", audience="notes-mcp")
# ok: mcp-server-exposed-without-auth
late.run(transport="http", host="0.0.0.0", port=8000)


# --- Low-level Server (SDK 2.x): auth is a parameter of the app factory ---

low = Server("notes-low")
# ruleid: mcp-server-exposed-without-auth
uvicorn.run(low.streamable_http_app(host="0.0.0.0"), host="0.0.0.0", port=8000)

# ok: mcp-server-exposed-without-auth
uvicorn.run(low.streamable_http_app(host="0.0.0.0", token_verifier=NotesTokenVerifier(), auth=AuthSettings(issuer_url="https://auth.example.com", resource_server_url="https://notes.example.com/mcp")), host="0.0.0.0", port=8000)


# --- Where the address comes from ---

BIND = os.environ.get("NOTES_BIND", "0.0.0.0")


def serve_from_env() -> None:
    # ruleid: mcp-server-exposed-without-auth
    notes.run("streamable-http", host=BIND, port=8000)


def serve_cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    # ruleid: mcp-server-exposed-without-auth
    notes.run("sse", host=args.host, port=args.port)


def serve_cli_local() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    # ok: mcp-server-exposed-without-auth
    notes.run("sse", host=args.host)


def serve_default(host: str = "0.0.0.0", port: int = 8000) -> None:
    # ruleid: mcp-server-exposed-without-auth
    notes.run("streamable-http", host=host, port=port)


def serve_default_local(host: str = "127.0.0.1", port: int = 8000) -> None:
    # ok: mcp-server-exposed-without-auth
    notes.run("streamable-http", host=host, port=port)


# --- Mounted in another ASGI app ---

site = Starlette(routes=[Mount("/", app=notes.sse_app())])
# ruleid: mcp-server-exposed-without-auth
uvicorn.run(site, host="0.0.0.0", port=8005)

api = FastAPI(title="notes")
api.mount("/mcp", notes.streamable_http_app())
# ruleid: mcp-server-exposed-without-auth
uvicorn.run(api, host="0.0.0.0", port=8006)

gated = Starlette(routes=[Mount("/", app=notes.sse_app())], middleware=[Middleware(ApiKeyMiddleware, header="x-api-key")])
# ok: mcp-server-exposed-without-auth
uvicorn.run(gated, host="0.0.0.0", port=8007)

gated_api = FastAPI(title="notes-gated")
gated_api.mount("/mcp", notes.streamable_http_app())
gated_api.add_middleware(ApiKeyMiddleware, header="x-api-key")
# ok: mcp-server-exposed-without-auth
uvicorn.run(gated_api, host="0.0.0.0", port=8008)


# --- Settings passed as a dict ---

LEGACY_HTTP = {"host": os.environ.get("LEGACY_BIND", "0.0.0.0"), "port": 8766}
# ruleid: mcp-server-exposed-without-auth
legacy_dict = FastMCP("legacy-dict", **LEGACY_HTTP)

LOCAL_HTTP = {"host": "127.0.0.1", "port": 8767}
# ok: mcp-server-exposed-without-auth
local_dict = FastMCP("local-dict", **LOCAL_HTTP)

GUARDED_HTTP = {
    "host": "0.0.0.0",
    "port": 8768,
    "auth": AuthSettings(issuer_url="https://auth.example.com", resource_server_url="https://notes.example.com"),
    "token_verifier": NotesTokenVerifier(),
}
# ok: mcp-server-exposed-without-auth
guarded_dict = FastMCP("guarded-dict", **GUARDED_HTTP)

RUN_OPTS = {"transport": "streamable-http", "host": "0.0.0.0", "port": 8009}
# ruleid: mcp-server-exposed-without-auth
notes.run(**RUN_OPTS)

UVICORN_OPTS = {"host": "::", "port": 8010, "log_level": "info"}
# ruleid: mcp-server-exposed-without-auth
uvicorn.run(asgi, **UVICORN_OPTS)

LOOPBACK_OPTS = {"host": "127.0.0.1", "port": 8011}
# ok: mcp-server-exposed-without-auth
uvicorn.run(asgi, **LOOPBACK_OPTS)
