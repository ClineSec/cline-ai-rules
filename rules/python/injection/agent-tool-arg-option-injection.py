import subprocess
from typing import Literal

from agents import function_tool
from crewai.tools import BaseTool as CrewBaseTool
from git import Repo
from langchain_core.tools import StructuredTool, tool
from mcp.server.mcpserver import MCPServer
from pydantic_ai import Agent, RunContext

agent = Agent("openai:gpt-5")
mcp = MCPServer("git-tools")
REPO = Repo("/srv/checkout")


@tool
def git_diff(target: str) -> str:
    """Diff the working tree against a target."""
    # ruleid: agent-tool-arg-option-injection
    return REPO.git.diff("--unified=3", target)


@tool
def git_diff_safe(target: str) -> str:
    """Diff against a target, with -- before it."""
    # ok: agent-tool-arg-option-injection
    return REPO.git.diff("--unified=3", "--", target)


@function_tool
def git_log(ref: str) -> str:
    """Show the log for a ref."""
    # ruleid: agent-tool-arg-option-injection
    return subprocess.run(["git", "log", "--oneline", ref], capture_output=True, text=True).stdout


@function_tool
def git_log_checked(ref: str) -> str:
    """Show the log for a ref that can't be an option."""
    if ref.startswith("-"):
        raise ValueError("refs can't start with '-'")
    # ok: agent-tool-arg-option-injection
    return subprocess.run(["git", "log", "--oneline", ref], capture_output=True, text=True).stdout


@agent.tool
def search_code(ctx: RunContext[None], pattern: str) -> str:
    """Search the checkout."""
    # ruleid: agent-tool-arg-option-injection
    return subprocess.run(["rg", "--json", pattern, "/srv/checkout"], capture_output=True, text=True).stdout


@agent.tool_plain
def fetch_branch(branch: str, remote: Literal["origin", "upstream"]) -> str:
    """Fetch a branch."""
    # ruleid: agent-tool-arg-option-injection
    subprocess.run(["git", "fetch", remote, branch], check=True)
    return "fetched"


def download(url: str) -> str:
    """Download a file."""
    # ruleid: agent-tool-arg-option-injection
    subprocess.run(("curl", "-fsSL", "--retry", "2", url), check=True)
    return "ok"


download_tool = StructuredTool.from_function(download)


class CheckoutTool(CrewBaseTool):
    name: str = "checkout"
    description: str = "Check out a branch."

    def _run(self, branch: str) -> str:
        # ruleid: agent-tool-arg-option-injection
        REPO.git.checkout(branch)
        return f"Switched to {branch}"


@mcp.tool()
def mcp_checkout(branch: str) -> str:
    # ok: agent-tool-arg-option-injection
    REPO.git.checkout(branch)
    return branch
