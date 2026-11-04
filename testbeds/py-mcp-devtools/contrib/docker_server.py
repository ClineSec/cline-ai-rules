"""Docker helpers for the coding agent (community contribution, standalone fastmcp)."""

import os
import subprocess

from fastmcp import FastMCP

docker = FastMCP("devtools-docker")

FORMAT = "{{.Names}}\t{{.Status}}\t{{.Image}}"


@docker.tool
def list_containers() -> str:
    """Running containers."""
    return subprocess.check_output(["docker", "ps", "--format", FORMAT], text=True)


@docker.tool
def container_exec(container: str, command: str) -> str:
    """Run a command inside a running container."""
    argv = ["docker", "exec", container, "sh", "-c", command]
    return subprocess.run(argv, capture_output=True, text=True, timeout=60).stdout


@docker.tool(name="container_logs")
def logs(container: str, tail: int = 100) -> str:
    """Recent logs of a container."""
    return subprocess.check_output(["docker", "logs", "--tail", str(tail), container], text=True)


if __name__ == "__main__":
    # DOCKER_MCP_HTTP=1 serves the tools on localhost for clients that only speak HTTP.
    if os.environ.get("DOCKER_MCP_HTTP"):
        docker.run(transport="http", port=int(os.environ.get("DOCKER_MCP_PORT", "8811")))
    else:
        docker.run()
