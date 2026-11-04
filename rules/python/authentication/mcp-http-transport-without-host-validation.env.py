import os

os.environ["FASTMCP_HOST"] = "0.0.0.0"

from fastmcp import FastMCP  # noqa: E402

inventory = FastMCP("inventory")

if __name__ == "__main__":
    # Bound to every interface through FASTMCP_HOST: mcp-server-exposed-without-auth reports it.
    # ok: mcp-http-transport-without-host-validation
    inventory.run(transport="http")


def serve_loopback():
    # An explicit host wins over FASTMCP_HOST: this one serves 127.0.0.1 with no Host check.
    # ruleid: mcp-http-transport-without-host-validation
    inventory.run(transport="http", host="127.0.0.1")
