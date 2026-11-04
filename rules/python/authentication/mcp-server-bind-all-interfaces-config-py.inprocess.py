import os

# ruleid: mcp-server-bind-all-interfaces-config-py
os.environ.setdefault("FASTMCP_HOST", "0.0.0.0")

from fastmcp import FastMCP  # noqa: E402

notes = FastMCP("notes")

if __name__ == "__main__":
    notes.run(transport="http")
