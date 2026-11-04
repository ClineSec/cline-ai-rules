"""Answers "is the service down?" tickets by having the Claude Code CLI check the status pages."""

import os
import subprocess

CLAUDE_BIN = os.environ.get("HELPDESK_CLAUDE_BIN", "claude")

STATUS_PAGES = "https://status.example.invalid"

# Tools for the outage checker: reading the runbooks and probing the status pages.
STATUS_TOOLS = ["Read", "Grep", "Bash(curl -s https://status.example.invalid/*)"]

# Tools for the runbook linker: read-only, plus one exact probe of the local health endpoint.
RUNBOOK_TOOLS = ["Read", "Grep", "Bash(curl -sf http://127.0.0.1:8000/healthz)"]


def check_outage(ticket_body: str) -> str:
    """Asks the agent whether the ticket describes a known outage."""
    prompt = (
        "A customer wrote the ticket below. Check the status pages under "
        f"{STATUS_PAGES} and say whether it matches a known outage.\n\n{ticket_body}"
    )
    result = subprocess.run(
        [CLAUDE_BIN, "-p", prompt, "--allowedTools", ",".join(STATUS_TOOLS)],
        capture_output=True,
        text=True,
        timeout=300,
        check=True,
    )
    return result.stdout


def link_runbooks(ticket_body: str) -> str:
    """Asks the agent which runbooks apply to the ticket."""
    result = subprocess.run(
        [
            CLAUDE_BIN,
            "-p",
            f"List the runbooks in docs/runbooks/ that apply to this ticket:\n\n{ticket_body}",
            "--allowedTools",
            *RUNBOOK_TOOLS,
            "--disallowedTools",
            "Bash(curl:*)",
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=True,
    )
    return result.stdout
