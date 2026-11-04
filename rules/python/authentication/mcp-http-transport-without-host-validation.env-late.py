import os

from fastmcp import FastMCP

inventory = FastMCP("inventory")

if __name__ == "__main__":
    # Too late: fastmcp read its settings at import, so this still serves 127.0.0.1 with no
    # Host check.
    os.environ.setdefault("FASTMCP_HOST", "0.0.0.0")
    # ruleid: mcp-http-transport-without-host-validation
    inventory.run(transport="http")
