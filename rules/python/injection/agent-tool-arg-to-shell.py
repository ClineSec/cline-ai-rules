import asyncio
import atexit
import os
import re
import shlex
import subprocess
from typing import Annotated, Literal, Optional

from agents import RunContextWrapper, function_tool
from crewai.tools import BaseTool as CrewBaseTool
from crewai.tools import tool as crew_tool
from langchain.agents import create_agent
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool, InjectedToolArg, StructuredTool, tool
from langgraph.prebuilt import ToolNode
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools import Tool as MCPTool
from pydantic import Field
from pydantic_ai import Agent, RunContext, Tool

mcp = FastMCP("devtools")
agent = Agent("openai:gpt-5")

ALLOWED_UNITS = {"nginx", "postgres"}
Unit = Literal["nginx", "postgres"]


# --- LangChain @tool ---------------------------------------------------------------------

@tool
def run_shell(command: str) -> str:
    """Run a shell command."""
    # ruleid: agent-tool-arg-to-shell
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout


@tool("grep_logs", parse_docstring=True)
def grep_logs(pattern: str, path: str = "/var/log/app.log") -> str:
    """Search the logs."""
    # ruleid: agent-tool-arg-to-shell
    return os.popen(f"grep -n {pattern} {path}").read()


@tool
def grep_logs_quoted(pattern: str) -> str:
    """Search the logs, quoting the pattern."""
    # ok: agent-tool-arg-to-shell
    return os.popen(f"grep -n {shlex.quote(pattern)} /var/log/app.log").read()


@tool
def grep_logs_argv(pattern: str) -> str:
    """Search the logs without a shell."""
    # ok: agent-tool-arg-to-shell
    return subprocess.run(["grep", "-n", "--", pattern, "/var/log/app.log"], capture_output=True, text=True).stdout


@tool
def restart_unit(unit: Literal["nginx", "postgres"], user_id: Annotated[str, InjectedToolArg]) -> str:
    """Restart a service. The model only picks the unit; the app injects user_id."""
    # ok: agent-tool-arg-to-shell
    os.system(f"systemctl restart {unit}")
    # ok: agent-tool-arg-to-shell
    return subprocess.getoutput(f"logger restart-by-{user_id}")


@tool
def tail_lines(count: int) -> str:
    """Tail the last lines of the log."""
    # ok: agent-tool-arg-to-shell
    return subprocess.getoutput(f"tail -n {count} /var/log/app.log")


@tool
def restart_checked(unit: str) -> str:
    """Restart a service from an allowlist."""
    if unit not in ALLOWED_UNITS:
        raise ValueError("unknown unit")
    # ok: agent-tool-arg-to-shell
    return subprocess.getoutput(f"systemctl restart {unit}")


@tool
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression."""
    # ruleid: agent-tool-arg-to-shell
    return str(eval(expression))


# --- LangChain StructuredTool.from_function, create_agent, ToolNode --------------------------

def disk_usage(path: str) -> str:
    """Report disk usage."""
    # ruleid: agent-tool-arg-to-shell
    return subprocess.check_output(f"du -sh {path}", shell=True, text=True)


disk_tool = StructuredTool.from_function(func=disk_usage, name="disk_usage", description="du")


def ping_host(host: str) -> str:
    """Ping a host."""
    # ruleid: agent-tool-arg-to-shell
    return subprocess.getoutput("ping -c 1 " + host)


ops_agent = create_agent("openai:gpt-5", tools=[ping_host, run_shell])


async def run_script(script: str) -> str:
    """Run a script with bash."""
    # ruleid: agent-tool-arg-to-shell
    proc = await asyncio.create_subprocess_exec("bash", "-c", script)
    return str(await proc.wait())


tool_node = ToolNode([run_script])


def not_registered(command: str) -> str:
    # ok: agent-tool-arg-to-shell
    return subprocess.getoutput(command)


# --- LangChain and CrewAI BaseTool subclasses ------------------------------------------------

class ShellTool(BaseTool):
    name: str = "shell"
    description: str = "Run a shell command."
    prefix: str = "set -e;"

    def _run(self, command: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        # ruleid: agent-tool-arg-to-shell
        return subprocess.getoutput(f"{self.prefix} {command}")

    async def _arun(self, command: str, run_manager=None) -> str:
        # ruleid: agent-tool-arg-to-shell
        proc = await asyncio.create_subprocess_shell(command)
        return str(await proc.wait())

    def describe(self, command: str) -> str:
        # ok: agent-tool-arg-to-shell
        return subprocess.getoutput(command)


class CrewShellTool(CrewBaseTool):
    name: str = "crew_shell"
    description: str = "Run a shell command."

    def _run(self, command: str) -> str:
        # ruleid: agent-tool-arg-to-shell
        return os.popen(command).read()


class NotATool:
    def _run(self, command: str) -> str:
        # ok: agent-tool-arg-to-shell
        return os.popen(command).read()


@crew_tool("Archive folder")
def archive_folder(folder: str) -> str:
    """Archive a folder."""
    # ruleid: agent-tool-arg-to-shell
    os.system("tar czf /tmp/archive.tgz " + folder)
    return "done"


# --- OpenAI Agents SDK -------------------------------------------------------------------------

@function_tool
def git_log(ctx: RunContextWrapper[None], ref: str) -> str:
    """Show the git log for a ref."""
    # ruleid: agent-tool-arg-to-shell
    out = subprocess.run(f"git log --oneline {ref}", shell=True, capture_output=True, text=True)
    # ok: agent-tool-arg-to-shell
    subprocess.run(f"echo {ctx}", shell=True)
    return out.stdout


@function_tool(name_override="branch_log")
def branch_log(branch: Annotated[str, Field(pattern=r"^[\w./-]+$")]) -> str:
    """Show the log for a validated branch name."""
    # ok: agent-tool-arg-to-shell
    return subprocess.getoutput(f"git log --oneline {branch}")


@function_tool
def checked_ref(ref: str) -> str:
    """Show the log for a ref checked with fullmatch."""
    if not re.fullmatch(r"[\w./-]+", ref):
        raise ValueError("bad ref")
    # ok: agent-tool-arg-to-shell
    return subprocess.getoutput(f"git log --oneline {ref}")


# --- pydantic-ai ------------------------------------------------------------------------------

@agent.tool
async def list_dir(ctx: RunContext[str], path: str) -> str:
    """List a directory."""
    # ruleid: agent-tool-arg-to-shell
    return subprocess.getoutput(f"ls -la {path}")


@agent.tool_plain
def word_count(path: str) -> str:
    """Count words in a file."""
    # ruleid: agent-tool-arg-to-shell
    return subprocess.getoutput(f"wc -w {path}")


def line_count(path: str) -> str:
    """Count lines in a file."""
    # ruleid: agent-tool-arg-to-shell
    return subprocess.getoutput(f"wc -l {path}")


def file_type(path: str) -> str:
    """Report a file's type."""
    # ruleid: agent-tool-arg-to-shell
    return subprocess.getoutput(f"file {path}")


line_tool = Tool(line_count, takes_ctx=False)
files_agent = Agent("openai:gpt-5", tools=[file_type])


def lookup_host(name: str) -> str:
    """Resolve a host name."""
    # ruleid: agent-tool-arg-to-shell
    return subprocess.getoutput("host " + name)


def bind_lookup(model):
    return model.bind_tools([lookup_host])


@tool
def restart_unit(unit: Unit) -> str:
    """Restart one of the allowed units."""
    # A Literal alias is as safe as the Literal written inline.
    # ok: agent-tool-arg-to-shell
    return subprocess.getoutput(f"systemctl restart {unit}")


def flush_cache(path: str) -> str:
    # Registered as an exit hook and with an MCP server, not with an agent framework.
    # ok: agent-tool-arg-to-shell
    return subprocess.getoutput(f"rm -rf {path}/cache")


atexit.register(flush_cache, "/tmp/app")
mcp.add_tool(MCPTool.from_function(flush_cache))


# --- Not agent tools: MCP tools belong to mcp-tool-arg-to-shell -----------------------------

@mcp.tool()
def mcp_shell(command: str) -> str:
    # ok: agent-tool-arg-to-shell
    return subprocess.getoutput(command)


# --- The command passed by keyword ------------------------------------------------------

@tool
def run_shell_keyword(command: str) -> str:
    """Run a shell command."""
    # ruleid: agent-tool-arg-to-shell
    return subprocess.run(args=command, shell=True, capture_output=True, text=True).stdout


@tool
def git_notes_keyword(note: str) -> str:
    """Attach a note to HEAD."""
    # ok: agent-tool-arg-to-shell
    return subprocess.run(args=["git", "notes", "add", "-m", note], capture_output=True, text=True).stdout
