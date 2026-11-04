"""Service status, disk usage, and log tails on the host running the server."""

import asyncio
import subprocess
from typing import Annotated, Literal

import anyio
from pydantic import Field

from devtools.app import mcp
from devtools.settings import settings

ALLOWED_UNITS = {"nginx", "app-web", "app-worker", "postgresql"}
TIMEOUT_S = 15


def _sh(command: str) -> str:
    """Run a shell pipeline and return combined output."""
    proc = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_S,
    )
    return (proc.stdout + proc.stderr).strip()


@mcp.tool()
def service_status(unit: str) -> str:
    """systemctl status for one unit."""
    return _sh(f"systemctl status --no-pager {unit} | head -n 20")


@mcp.tool()
def service_status_checked(unit: str) -> str:
    """systemctl status for an allowlisted unit."""
    if unit not in ALLOWED_UNITS:
        return f"Unknown unit {unit!r}; expected one of {sorted(ALLOWED_UNITS)}"
    return _sh(f"systemctl status --no-pager {unit} | head -n 20")


@mcp.tool()
async def disk_usage(path: str = "/srv") -> str:
    """Disk usage for a folder, largest entries first."""
    proc = await asyncio.create_subprocess_shell(
        f"du -sh {path}/* 2>/dev/null | sort -rh | head -n 15",
        stdout=asyncio.subprocess.PIPE,
    )
    out, _ = await proc.communicate()
    return out.decode()


@mcp.tool()
async def tail_log(
    name: Annotated[str, Field(pattern=r"^[a-z0-9_-]+\.log$")],
    lines: Annotated[int, Field(ge=1, le=500)] = 100,
) -> str:
    """Last lines of a log file in the app log folder."""
    result = await anyio.run_process(f"tail -n {lines} {settings.log_dir}/{name}")
    return result.stdout.decode()


@mcp.tool()
async def grep_log(name: str, needle: str) -> str:
    """Matching lines from a log file in the app log folder."""
    cmd = f"grep -n -- {needle} {settings.log_dir}/{name} | tail -n 50"
    result = await anyio.run_process(cmd, check=False)
    return result.stdout.decode()


@mcp.tool()
def top_processes(sort: Literal["cpu", "mem"] = "cpu", count: int = 10) -> str:
    """The busiest processes."""
    return _sh(f"ps aux --sort=-%{sort} | head -n {count + 1}")


@mcp.tool()
def uptime() -> str:
    """Load averages."""
    return subprocess.check_output("uptime", shell=True, text=True).strip()
