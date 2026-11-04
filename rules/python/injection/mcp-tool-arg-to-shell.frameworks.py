# Other ways to register a tool: MCP SDK v1 (FastMCP and the low-level Server), standalone
# fastmcp, and the Claude Agent SDK's in-process MCP tools.
import os
import subprocess

import mcp.types as types
from claude_agent_sdk import tool as sdk_tool
from fastmcp import FastMCP as StandaloneFastMCP
from fastmcp.tools import Tool, tool
from mcp.server import Server
from mcp.server.fastmcp import FastMCP

v1 = FastMCP("ops")
fm = StandaloneFastMCP("ops2")
low = Server("ops3")


@v1.tool()
def restart(service: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.check_output("systemctl restart " + service, shell=True, text=True)


@fm.tool
def which(binary: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.getoutput(f"which {binary}")


@tool(name="checksum")
def checksum(path: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return os.popen(f"sha256sum {path}").read()


def compress(folder: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.check_output(f"tar czf /tmp/out.tgz {folder}", shell=True, text=True)


fm.add_tool(Tool.from_function(compress))


@low.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "lint":
        # ruleid: mcp-tool-arg-to-shell
        out = subprocess.run(f"ruff check {arguments['path']}", shell=True, capture_output=True)
        return [types.TextContent(type="text", text=out.stdout.decode())]
    return []


@sdk_tool("search_repo", "Search the repository", {"query": str})
async def search_repo(args):
    # ruleid: mcp-tool-arg-to-shell
    out = subprocess.getoutput("rg --json " + args["query"])
    return {"content": [{"type": "text", "text": out}]}


# --- Near misses ---


@fm.tool
def which_safe(binary: str) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.run(["which", binary], capture_output=True, text=True).stdout


@fm.resource("config://{name}")
def config(name: str) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.getoutput("cat /etc/app/defaults.toml")


@low.call_tool()
async def handle_fixed(name: str, arguments: dict) -> list[types.TextContent]:
    # ok: mcp-tool-arg-to-shell
    out = subprocess.run("uptime", shell=True, capture_output=True)
    return [types.TextContent(type="text", text=out.stdout.decode())]
