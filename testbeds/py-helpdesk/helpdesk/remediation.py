"""Background remediation: let the assistant apply its one-line fix on the helpdesk host."""

import asyncio
import logging
from asyncio import create_subprocess_shell
from dataclasses import dataclass

from .llm import TRIAGE_MODEL, claude_async

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Runbook:
    shell_prefix: str = "set -eu;"
    timeout: float = 30.0


DEFAULT_RUNBOOK = Runbook()


async def remediate(ticket_text: str, runbook: Runbook = DEFAULT_RUNBOOK) -> str:
    reply = await claude_async.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=256,
        system="Reply with one shell command that fixes the ticket and nothing else.",
        messages=[{"role": "user", "content": ticket_text}],
    )
    fix = reply.content[0].text.strip()
    script = f"{runbook.shell_prefix} {fix}"
    log.info("remediating: %s", script)
    proc = await create_subprocess_shell(
        script, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    out, _ = await asyncio.wait_for(proc.communicate(), runbook.timeout)
    return out.decode()


async def log_summary(ticket_text: str) -> None:
    """Write a one-line summary of the ticket to syslog for the on-call dashboard."""
    reply = await claude_async.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=64,
        system="Summarise the ticket in one line.",
        messages=[{"role": "user", "content": ticket_text}],
    )
    summary = reply.content[0].text.strip()
    # The command is fixed; the summary only ever arrives on stdin.
    proc = await create_subprocess_shell(
        "logger -t helpdesk-summary", stdin=asyncio.subprocess.PIPE
    )
    await proc.communicate(summary.encode())
