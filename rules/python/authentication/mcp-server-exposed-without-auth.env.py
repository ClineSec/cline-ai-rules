"""Release-notes server for the build farm, started with `python release_notes.py`."""

import os

# fastmcp reads its settings when it is first imported, so these must come first.
os.environ.setdefault("FASTMCP_HOST", "0.0.0.0")
os.environ.setdefault("FASTMCP_PORT", "8031")

from fastmcp import FastMCP  # noqa: E402
from fastmcp.server.auth.providers.jwt import JWTVerifier  # noqa: E402

notes = FastMCP("release-notes")
secured_notes = FastMCP("release-notes-secured", auth=JWTVerifier(jwks_uri="https://auth.example.com/jwks"))


@notes.tool
def latest(component: str) -> str:
    return f"no notes for {component}"


def serve_http():
    # ruleid: mcp-server-exposed-without-auth
    notes.run(transport="http")


async def serve_sse():
    # ruleid: mcp-server-exposed-without-auth
    await notes.run_async("sse")


async def serve_streamable():
    # ruleid: mcp-server-exposed-without-auth
    await notes.run_http_async(port=8032)


def serve_local():
    # An explicit host wins over the settings.
    # ok: mcp-server-exposed-without-auth
    notes.run(transport="http", host="127.0.0.1")


def serve_stdio():
    # stdio never listens on a port.
    # ok: mcp-server-exposed-without-auth
    notes.run()


def serve_secured():
    # ok: mcp-server-exposed-without-auth
    secured_notes.run(transport="http")
