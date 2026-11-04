import os

os.environ["FASTMCP_HOST"] = "0.0.0.0"
os.putenv("FASTMCP_HOST", "0.0.0.0")

import fastmcp  # noqa: E402,F401  (imported for its client elsewhere)
from mcp.server.fastmcp import FastMCP  # noqa: E402

# The MCP SDK's FastMCP passes host="127.0.0.1" to its settings from 1.12.3 on, which wins
# over FASTMCP_HOST.
lookup = FastMCP("lookup")


@lookup.tool()
def owner(service: str) -> str:
    return f"{service}: platform team"


if __name__ == "__main__":
    # ok: mcp-server-exposed-without-auth
    lookup.run(transport="streamable-http")
