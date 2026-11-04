import os

from fastmcp import FastMCP

triage = FastMCP("triage")


@triage.tool
def summarize(run_id: str) -> str:
    return f"run {run_id}"


if __name__ == "__main__":
    # Set after fastmcp was imported: its settings were already read, so the server still
    # binds 127.0.0.1.
    os.environ["FASTMCP_HOST"] = "0.0.0.0"
    # ok: mcp-server-exposed-without-auth
    triage.run(transport="http")
