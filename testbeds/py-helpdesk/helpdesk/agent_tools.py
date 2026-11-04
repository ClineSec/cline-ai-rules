"""LangChain tools the helpdesk agent can call while it works a ticket.

The LangGraph agent picks a tool and fills in its arguments from the ticket thread, so the
requester's text reaches every str parameter below.
"""

import shlex
import subprocess
from pathlib import Path
from typing import Annotated, Literal, Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool, InjectedToolArg, StructuredTool, tool
from langgraph.prebuilt import create_react_agent

from .llm import PLANNER_MODEL

RUNBOOK_DIR = Path("/srv/helpdesk/runbooks")
PRINTERS = {"floor2-color", "floor2-mono", "lobby"}


def _local(command: str) -> str:
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return result.stdout


@tool
def ping_host(host: str) -> str:
    """Check whether a host on the office network answers ping."""
    out = subprocess.run(f"ping -c 2 -W 1 {host}", shell=True, capture_output=True, text=True)
    return out.stdout or out.stderr


@tool
def ping_host_quoted(host: str) -> str:
    """Same check, quoting the host name for the shell."""
    out = subprocess.run(f"ping -c 2 -W 1 {shlex.quote(host)}", shell=True, capture_output=True, text=True)
    return out.stdout or out.stderr


@tool
def restart_service(
    unit: Literal["cups", "sssd", "vpn-agent"],
    ticket_id: Annotated[str, InjectedToolArg],
) -> str:
    """Restart one of the services the helpdesk is allowed to bounce."""
    subprocess.run(f"sudo systemctl restart {unit}", shell=True, check=True)
    return subprocess.getoutput(f"logger -t helpdesk restarted-{unit}-for-{ticket_id}")


@tool
def lookup_dns(name: str) -> str:
    """Resolve a host name with the office resolver."""
    return _local("dig +short " + name)


def runbook_history(ref: str) -> str:
    """Show recent changes to the runbooks at a ref."""
    out = subprocess.run(
        ["git", "-C", str(RUNBOOK_DIR), "log", "--oneline", "-n", "20", ref],
        capture_output=True,
        text=True,
    )
    return out.stdout


def runbook_diff(ref: str) -> str:
    """Show what changed in the runbooks since a ref."""
    out = subprocess.run(
        ["git", "-C", str(RUNBOOK_DIR), "diff", "--stat", "--end-of-options", ref],
        capture_output=True,
        text=True,
    )
    return out.stdout


class PrintQueueTool(BaseTool):
    name: str = "print_queue"
    description: str = "List the jobs waiting on a printer."

    def _run(self, printer: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        if printer not in PRINTERS:
            return f"Unknown printer {printer!r}."
        return _local(f"lpstat -o {printer}")


class PrinterStatusTool(BaseTool):
    name: str = "printer_status"
    description: str = "Show whether a printer is accepting jobs."

    def _run(self, printer: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return subprocess.getoutput(f"lpstat -p {printer} -a")


TOOLS = [
    ping_host,
    ping_host_quoted,
    restart_service,
    lookup_dns,
    StructuredTool.from_function(runbook_history),
    StructuredTool.from_function(runbook_diff),
    PrintQueueTool(),
    PrinterStatusTool(),
]

helpdesk_agent = create_react_agent(PLANNER_MODEL, tools=TOOLS)
