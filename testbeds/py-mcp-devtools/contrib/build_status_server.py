"""Build status for the coding agents in the CI containers (standalone fastmcp).

Runs on the build VM as `python contrib/build_status_server.py`, so the agents in the job
containers can reach it over the bridge network. fastmcp reads its settings once, when it is
first imported, so the bind address and port are set before the import.
"""

import os
import subprocess

os.environ.setdefault("FASTMCP_HOST", "0.0.0.0")
os.environ.setdefault("FASTMCP_PORT", "8044")

from fastmcp import FastMCP  # noqa: E402

BUILDS_DIR = "/srv/builds"

status = FastMCP("build-status", instructions="Recent builds and their logs on the build VM.")


@status.tool
def recent_builds(branch: str, limit: int = 10) -> str:
    """List the newest builds of a branch."""
    out = subprocess.run(
        args=f"ls -1t {BUILDS_DIR}/{branch} | head -n {limit}",
        shell=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return out.stdout


@status.tool
def build_log(build_id: str, lines: int = 100) -> str:
    """Tail one build's log."""
    out = subprocess.run(
        args=["tail", "-n", str(lines), "--", f"{BUILDS_DIR}/logs/{build_id}.log"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return out.stdout


if __name__ == "__main__":
    status.run(transport="http")
