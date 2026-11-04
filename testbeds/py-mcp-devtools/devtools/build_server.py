"""Build targets for the checkout, on the SDK's low-level Server.

Kept separate from the main server so the build tools can run in a container with the
toolchain installed. Tool descriptors are hand-written so the schemas match the Makefile.
"""

import asyncio
from typing import Any

import mcp.types as types
from mcp.server.context import ServerRequestContext
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from devtools.settings import settings

MAKE_TARGETS = ("build", "test", "lint", "docs")

TOOLS = [
    types.Tool(
        name="make",
        description="Run a Makefile target in the checkout.",
        input_schema={
            "type": "object",
            "properties": {
                "target": {"type": "string", "enum": list(MAKE_TARGETS)},
                "jobs": {"type": "integer", "minimum": 1, "maximum": 8},
            },
            "required": ["target"],
        },
    ),
    types.Tool(
        name="run_tests",
        description="Run pytest with an optional -k expression.",
        input_schema={
            "type": "object",
            "properties": {"keyword": {"type": "string"}},
        },
    ),
]


async def _run(argv: list[str]) -> str:
    proc = await asyncio.create_subprocess_exec(
        *argv,
        cwd=settings.repo_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    return out.decode()[-20_000:]


async def list_tools(
    ctx: ServerRequestContext[Any], params: types.PaginatedRequestParams | None
) -> types.ListToolsResult:
    return types.ListToolsResult(tools=TOOLS)


async def call_tool(ctx: ServerRequestContext[Any], params: types.CallToolRequestParams) -> types.CallToolResult:
    args = params.arguments or {}
    if params.name == "make":
        target = args["target"]
        if target not in MAKE_TARGETS:
            raise ValueError(f"unknown target {target!r}")
        text = await _run(["make", f"-j{int(args.get('jobs', 2))}", target])
    elif params.name == "run_tests":
        keyword = args.get("keyword", "")
        proc = await asyncio.create_subprocess_shell(
            f"python -m pytest -q -k '{keyword}'",
            cwd=settings.repo_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        out, _ = await proc.communicate()
        text = out.decode()[-20_000:]
    else:
        raise ValueError(f"unknown tool {params.name!r}")
    return types.CallToolResult(content=[types.TextContent(text=text)])


server = Server("devtools-build", on_list_tools=list_tools, on_call_tool=call_tool)


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
