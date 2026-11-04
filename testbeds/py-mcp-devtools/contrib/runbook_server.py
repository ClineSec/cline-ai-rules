"""Runbook templates for the coding agent (community contribution, standalone fastmcp).

Serves a runbook page per service and a prompt that walks through a failing unit. The template
and prompt functions are plain functions so the team's other fastmcp servers can register them
too.
"""

import shlex
import subprocess
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.resources import ResourceTemplate

RUNBOOKS = Path("/srv/devtools/runbooks")

runbook = FastMCP("devtools-runbook")


def render_runbook(page: str) -> str:
    """A runbook page rendered for the terminal."""
    return subprocess.getoutput(f"pandoc -t plain {RUNBOOKS}/{page}.md")


def unit_walkthrough(unit: str) -> str:
    """Walk through a failing unit: its status, then what to check next."""
    status = subprocess.getoutput("systemctl status --no-pager " + shlex.quote(unit))
    return f"This unit is failing. Explain the status below and list what to check next:\n{status}"


def unit_dependencies(unit: str) -> str:
    """The units a unit depends on, for checking whether one of them failed first."""
    deps = subprocess.check_output(f"systemctl list-dependencies --plain {unit}", shell=True, text=True)
    return f"Check which of these dependencies failed before {unit}:\n{deps}"


@runbook.resource("runbook://{page}/source")
def runbook_source(page: str) -> str:
    """The runbook page's Markdown source."""
    return (RUNBOOKS / f"{Path(page).name}.md").read_text()


runbook.add_template(ResourceTemplate.from_function(render_runbook, uri_template="runbook://{page}/plain"))
runbook.add_prompt(unit_walkthrough)
runbook.add_prompt(unit_dependencies)


if __name__ == "__main__":
    runbook.run()
