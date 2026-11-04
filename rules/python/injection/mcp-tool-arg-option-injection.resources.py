import subprocess

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("git-resources")


@mcp.resource("git://diff/{ref}")
def diff(ref: str) -> str:
    # ruleid: mcp-tool-arg-option-injection
    return subprocess.run(["git", "diff", ref], capture_output=True, text=True).stdout


@mcp.prompt()
def review_branch(branch: str) -> str:
    # ruleid: mcp-tool-arg-option-injection
    log = subprocess.run(["git", "log", "--oneline", branch], capture_output=True, text=True).stdout
    return f"Review these commits:\n{log}"


@mcp.resource("git://show/{ref}")
def show_safe(ref: str) -> str:
    # ok: mcp-tool-arg-option-injection
    return subprocess.run(["git", "show", "--end-of-options", ref], capture_output=True, text=True).stdout
