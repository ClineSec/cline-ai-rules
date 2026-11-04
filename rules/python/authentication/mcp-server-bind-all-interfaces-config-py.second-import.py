import os

from fastmcp import Client

# Set after the first fastmcp import, so the later import doesn't read it either.
# ok: mcp-server-bind-all-interfaces-config-py
os.environ.update(FASTMCP_HOST="0.0.0.0")

from fastmcp import FastMCP  # noqa: E402

relay = FastMCP("relay")
upstream = Client("http://127.0.0.1:8100/mcp")
