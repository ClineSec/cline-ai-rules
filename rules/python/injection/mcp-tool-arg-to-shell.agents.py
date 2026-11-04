# Agent-framework tools are agent-tool-arg-to-shell's, not this rule's: LangChain's and
# CrewAI's @tool resolve to <module>.tool, and pydantic-ai's @agent.tool looks like
# @server.tool, so each must stay out of the MCP sources.
import subprocess

from crewai.tools import tool as crew_tool
from langchain_core.tools import tool
from mcp.server.mcpserver import MCPServer
from pydantic_ai import Agent, RunContext

mcp = MCPServer("ops")
agent = Agent("openai:gpt-5")


@tool
def lc_shell(command: str) -> str:
    """Run a command."""
    # ok: mcp-tool-arg-to-shell
    return subprocess.getoutput(command)


@crew_tool("Shell")
def crew_shell(command: str) -> str:
    """Run a command."""
    # ok: mcp-tool-arg-to-shell
    return subprocess.getoutput(command)


@agent.tool
def pai_shell(ctx: RunContext[None], command: str) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.getoutput(command)


@agent.tool(retries=2)
def pai_shell_retry(ctx: RunContext, command: str) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.getoutput(command)


@mcp.tool()
def mcp_shell(command: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.getoutput(command)
