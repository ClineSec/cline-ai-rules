"""Runbook resources and incident prompts for the ops hosts (MCP Python SDK 2.x).

Clients show these beside the tools: a journal page per service, CI failure briefs, and a prompt
that drafts a branch review. Runs on its own: `python -m devtools.runbooks`.
"""

import asyncio
import os
import sqlite3
import subprocess
from contextlib import closing
from typing import Literal

from mcp.server.mcpserver import MCPServer

from devtools.settings import settings

runbooks = MCPServer(
    "devtools-runbooks",
    instructions="Runbooks, service journals, and incident prompts for the ops hosts.",
)

RUNBOOK_DIR = settings.repo_root / "docs" / "runbooks"
RUNS_DB = settings.repo_root / ".ci" / "runs.sqlite"
# The services this host runs; status pages exist only for these.
HostService = Literal["devtools-notes", "devtools-containers", "nginx"]
# The environment the server started with, kept to diff against a fresh login shell.
BOOT_ENV = os.environ.copy()



@runbooks.resource("runbook://index", mime_type="application/json")
def runbook_index() -> list[str]:
    """Every runbook page in the checkout."""
    return sorted(page.stem for page in RUNBOOK_DIR.glob("*.md"))


@runbooks.resource("runbook://{service}/journal", mime_type="text/plain")
async def service_journal(service: str) -> str:
    """The last 100 journal lines for a service."""
    proc = await asyncio.create_subprocess_shell(
        f"journalctl -u {service} -n 100 --no-pager",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    return out.decode(errors="replace")


@runbooks.resource("runbook://{service}/status", mime_type="text/plain")
def service_status(service: HostService) -> str:
    """systemctl status for one of the services this host runs."""
    return subprocess.run(
        f"systemctl status --no-pager {service}", shell=True, capture_output=True, text=True
    ).stdout


@runbooks.resource("devtools://runtime/boot-environment", mime_type="application/json")
def boot_environment() -> dict[str, str]:
    """The environment the server started with, to compare against a fresh shell."""
    return BOOT_ENV


@runbooks.resource("devtools://runtime/timezone", mime_type="text/plain")
def timezone_setting() -> str:
    """The server's TZ, for reading journal timestamps."""
    return os.environ.get("TZ", "UTC")


@runbooks.prompt()
def failing_jobs_brief(branch: str) -> str:
    """Draft a short brief about the jobs failing on a branch."""
    with closing(sqlite3.connect(f"file:{RUNS_DB}?mode=ro", uri=True)) as runs:
        rows = runs.execute(
            f"SELECT job, started_at FROM runs WHERE branch = '{branch}' AND status = 'failed' LIMIT 20"
        ).fetchall()
    lines = "\n".join(f"- {job} at {started}" for job, started in rows)
    return f"Summarize why these jobs fail on {branch} and who should look:\n{lines}"


@runbooks.prompt()
def slow_jobs_brief(branch: str) -> str:
    """Draft a brief about the slowest jobs on a branch."""
    with closing(sqlite3.connect(f"file:{RUNS_DB}?mode=ro", uri=True)) as runs:
        rows = runs.execute(
            "SELECT job, duration_s FROM runs WHERE branch = ? ORDER BY duration_s DESC LIMIT 10", (branch,)
        ).fetchall()
    lines = "\n".join(f"- {job}: {seconds}s" for job, seconds in rows)
    return f"Suggest how to speed up these jobs on {branch}:\n{lines}"


@runbooks.prompt()
def review_branch(branch: str) -> str:
    """Ask for a review of the commits on a branch."""
    log = subprocess.run(
        ["git", "log", "--oneline", "-n", "30", branch],
        cwd=settings.repo_root,
        capture_output=True,
        text=True,
    ).stdout
    return f"Review these commits for risky changes:\n{log}"


@runbooks.prompt()
def review_branch_since(branch: str, since: str = "1 week ago") -> str:
    """Ask for a review of a branch's recent commits."""
    log = subprocess.run(
        ["git", "log", "--oneline", f"--since={since}", "--end-of-options", branch],
        cwd=settings.repo_root,
        capture_output=True,
        text=True,
    ).stdout
    return f"Review these recent commits:\n{log}"


if __name__ == "__main__":
    runbooks.run()
