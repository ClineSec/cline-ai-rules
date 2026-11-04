import os

# The MCP SDK's FastMCP passes host="127.0.0.1" to its settings from 1.12.3 on, which wins.
# ok: mcp-server-bind-all-interfaces-config-py
os.environ["FASTMCP_HOST"] = "0.0.0.0"

from mcp.server.fastmcp import FastMCP  # noqa: E402

lookup = FastMCP("lookup")

if __name__ == "__main__":
    lookup.run(transport="streamable-http")
