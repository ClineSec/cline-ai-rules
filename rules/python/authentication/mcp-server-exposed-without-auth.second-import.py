import os

from fastmcp import Client

os.environ["FASTMCP_HOST"] = "0.0.0.0"

from fastmcp import FastMCP  # noqa: E402

relay = FastMCP("relay")
upstream = Client("http://127.0.0.1:8100/mcp")

if __name__ == "__main__":
    # fastmcp read its settings at the first import (for Client), before FASTMCP_HOST was set.
    # ok: mcp-server-exposed-without-auth
    relay.run(transport="http")
