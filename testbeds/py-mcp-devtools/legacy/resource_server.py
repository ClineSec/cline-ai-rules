"""Service journals as MCP resources on the 1.x low-level server, for clients pinned to 1.x.

The handlers get the raw URI and prompt arguments; there's no per-argument validation here.
"""

import subprocess

import mcp.types as types
from mcp.server import Server
from pydantic import AnyUrl

server = Server("devtools-legacy-resources")

KNOWN_UNITS = {"devtools-notes", "devtools-containers", "nginx"}


@server.read_resource()
async def read_journal(uri: AnyUrl) -> str:
    unit = str(uri).removeprefix("journal://")
    return subprocess.getoutput(f"journalctl -u {unit} -n 50 --no-pager")


@server.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
    args = arguments or {}
    if name == "unit-status":
        unit = args.get("unit", "")
        status = subprocess.run(
            "systemctl is-active " + unit, shell=True, capture_output=True, text=True
        ).stdout
        text = f"The unit reports {status.strip()}. Explain what that means."
    elif name == "known-unit-status" and args.get("unit") in KNOWN_UNITS:
        status = subprocess.run(["systemctl", "is-active", args["unit"]], capture_output=True, text=True).stdout
        text = f"The unit reports {status.strip()}."
    else:
        text = "Unknown prompt."
    return types.GetPromptResult(
        messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))]
    )
