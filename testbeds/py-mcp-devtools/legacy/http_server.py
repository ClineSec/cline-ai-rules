"""The 1.x ops server over SSE, for the dashboard VM whose MCP client can't spawn stdio servers.

Runs next to ops_server.py on the same SDK pin. Only read-only status tools live here.
"""

import os
import subprocess

from mcp.server.fastmcp import FastMCP

# The VM's firewall only opens the port to the office VPN, so listen on every interface.
# Kept in one place so the dashboard VM's systemd unit and this file agree on the paths.
HTTP_SETTINGS = {
    "host": os.environ.get("DEVTOOLS_LEGACY_BIND", "0.0.0.0"),
    "port": int(os.environ.get("DEVTOOLS_LEGACY_PORT", "8766")),
    "sse_path": "/sse",
    "message_path": "/messages/",
    "log_level": os.environ.get("DEVTOOLS_LEGACY_LOG_LEVEL", "INFO"),
}

mcp = FastMCP("devtools-legacy-http", **HTTP_SETTINGS)


@mcp.tool()
def uptime() -> str:
    """Load averages for the VM."""
    return subprocess.run(["uptime"], capture_output=True, text=True).stdout


@mcp.tool()
def disk_report() -> str:
    """Free space on the data volume."""
    return subprocess.run(["df", "-h", "/srv"], capture_output=True, text=True).stdout


if __name__ == "__main__":
    mcp.run(transport="sse")
