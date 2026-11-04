"""devtools ops tools on MCP Python SDK 1.x, for clients that can't move to 2.x yet."""

import os
import subprocess

from mcp.server.fastmcp import Context, FastMCP

mcp = FastMCP("devtools-legacy")

REPO_ROOT = os.environ.get("DEVTOOLS_REPO", "/srv/checkout")


@mcp.tool()
async def service_status(unit: str, ctx: Context) -> str:
    """systemctl status for one unit."""
    await ctx.info(f"checking {unit}")
    return subprocess.getoutput("systemctl status --no-pager " + unit)


@mcp.tool()
def git_log(ref: str = "HEAD") -> str:
    """One-line history for a ref."""
    return subprocess.run(
        ["git", "log", "--oneline", "-n", "20", "--end-of-options", ref],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    ).stdout


@mcp.tool()
def disk_free() -> str:
    """Free space on the data volume."""
    return os.popen("df -h /srv").read()


if __name__ == "__main__":
    mcp.run()
