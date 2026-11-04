import os

from fastmcp import Client

os.environ["FASTMCP_HOST"] = "0.0.0.0"

from fastmcp import FastMCP  # noqa: E402

relay = FastMCP("relay")
upstream = Client("http://127.0.0.1:8100/mcp")

if __name__ == "__main__":
    # fastmcp was first imported (for Client) before FASTMCP_HOST was set, so this still serves
    # 127.0.0.1, with no Host check.
    # ruleid: mcp-http-transport-without-host-validation
    relay.run(transport="http")
