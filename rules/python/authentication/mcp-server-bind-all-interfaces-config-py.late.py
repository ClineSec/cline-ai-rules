import os

from fastmcp import FastMCP

notes = FastMCP("notes")

if __name__ == "__main__":
    # fastmcp already read its settings at import, so this changes nothing.
    # ok: mcp-server-bind-all-interfaces-config-py
    os.environ["FASTMCP_HOST"] = "0.0.0.0"
    notes.run(transport="http")
