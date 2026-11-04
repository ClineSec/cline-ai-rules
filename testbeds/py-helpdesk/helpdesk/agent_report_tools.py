"""Report tools for the LangGraph helpdesk agent (see agent_tools.py for the ticket tools).

The agent writes small pandas snippets against the nightly export while it works a ticket,
so it can say "you are the third reopen this week" without a human pulling numbers.
"""

import subprocess
import sys
from typing import Literal

from langchain_core.tools import tool

EXPORT_DIR = "/srv/helpdesk/exports"


@tool
def run_report_snippet(code: str) -> str:
    """Run a short pandas snippet against the ticket export and return what it prints."""
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=EXPORT_DIR,
    )
    return out.stdout[-4000:] or out.stderr[-4000:]


@tool
def run_saved_report(name: Literal["weekly_volume", "sla_breaches", "reopen_rate"]) -> str:
    """Run one of the reviewed reports by name."""
    out = subprocess.run(
        [sys.executable, "-m", f"helpdesk.reports.{name}"],
        capture_output=True,
        text=True,
        cwd=EXPORT_DIR,
    )
    return out.stdout[-4000:]
