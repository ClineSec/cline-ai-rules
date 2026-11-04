"""Printer queue fixes the assistant suggests, applied on the print server or a kiosk."""

import logging
import subprocess

import paramiko

from .llm import PLANNER_MODEL, openai_client

log = logging.getLogger(__name__)

FIX_PROMPT = (
    "You fix CUPS printer queues. Reply with one shell command for the print server and "
    "nothing else."
)


def _suggest(ticket_text: str) -> str:
    response = openai_client.responses.create(
        model=PLANNER_MODEL, instructions=FIX_PROMPT, input=ticket_text
    )
    return response.output_text.strip()


def apply_queue_fix(ticket_text: str) -> str:
    fix = _suggest(ticket_text)
    log.info("applying printer fix: %s", fix)
    result = subprocess.run(
        args=fix,
        shell=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result.stdout


def apply_kiosk_fix(kiosk_host: str, ticket_text: str) -> str:
    fix = _suggest(ticket_text)
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.connect(kiosk_host, username="helpdesk")
    try:
        _, stdout, _ = ssh.exec_command(command=fix, timeout=60)
        return stdout.read().decode()
    finally:
        ssh.close()


def queue_status(printer: str, ticket_text: str) -> str:
    """The suggestion only goes into the audit note; the command itself is fixed."""
    suggestion = _suggest(ticket_text)
    result = subprocess.run(
        args=["lpstat", "-p", printer],
        capture_output=True,
        text=True,
        timeout=10,
        env={"HELPDESK_SUGGESTION": suggestion},
    )
    return result.stdout
