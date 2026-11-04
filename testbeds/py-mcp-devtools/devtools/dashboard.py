"""Read-only build and repository status for the ops dashboard, served over streamable HTTP.

The dashboard polls this next to the /healthz route, so both live in one Starlette app:

    python -m devtools.dashboard --port 9100
"""

import argparse
import contextlib
import subprocess

import uvicorn
from mcp.server.mcpserver import MCPServer
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Mount, Route

from devtools.settings import settings

status = MCPServer(
    "devtools-status",
    instructions="Status for the dashboard. Every tool is read-only.",
)


@status.tool()
def head_commit() -> str:
    """The commit the checkout is on."""
    return subprocess.run(
        ["git", "log", "-1", "--format=%H %s"], cwd=settings.repo_root, capture_output=True, text=True
    ).stdout


@status.tool()
def dirty_files() -> list[str]:
    """Files with uncommitted changes."""
    out = subprocess.run(["git", "status", "--porcelain"], cwd=settings.repo_root, capture_output=True, text=True)
    return [line[3:] for line in out.stdout.splitlines()]


async def healthz(request: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    async with status.session_manager.run():
        yield


def main() -> None:
    parser = argparse.ArgumentParser(description="devtools dashboard status server")
    parser.add_argument("--host", default="0.0.0.0", help="interface to listen on (the dashboard runs in another container)")
    parser.add_argument("--port", type=int, default=9100)
    args = parser.parse_args()

    app = Starlette(
        routes=[Route("/healthz", healthz), Mount("/", app=status.streamable_http_app())],
        lifespan=lifespan,
    )
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
