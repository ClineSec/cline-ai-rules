"""MCP server that lets the IT team's coding agents chart helpdesk data.

Run with `python -m helpdesk.mcp_reports` from an MCP client config (stdio).
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal

from mcp.server.mcpserver import MCPServer

EXPORT_DIR = Path("/srv/helpdesk/exports")
CHART_DIR = Path("/srv/helpdesk/charts")

mcp = MCPServer("helpdesk-reports")


@mcp.tool()
def render_chart(script: str, title: str) -> str:
    """Run a matplotlib script against the ticket export and save the chart as a PNG."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir=CHART_DIR) as handle:
        handle.write(script)
    out_png = CHART_DIR / f"{title.lower().replace(' ', '-')}.png"
    subprocess.run([sys.executable, handle.name, str(out_png)], check=True, timeout=60, cwd=EXPORT_DIR)
    return str(out_png)


@mcp.tool()
def save_chart_notes(title: str, notes: str) -> str:
    """Store the agent's notes next to a chart and stage them for review."""
    path = CHART_DIR / f"{title.lower().replace(' ', '-')}.md"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(notes)
    subprocess.run(["git", "-C", str(CHART_DIR), "add", "--", path.name], check=True)
    return str(path)


@mcp.tool()
def standard_chart(kind: Literal["volume", "backlog", "sla"]) -> str:
    """Render one of the standard charts."""
    subprocess.run([sys.executable, "-m", f"helpdesk.charts.{kind}"], check=True, cwd=EXPORT_DIR)
    return str(CHART_DIR / f"{kind}.png")


if __name__ == "__main__":
    mcp.run()
