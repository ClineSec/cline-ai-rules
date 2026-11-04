"""Run diagnostics the assistant proposes for a ticket."""

import logging
import subprocess

from .llm import PLANNER_MODEL, claude, TRIAGE_MODEL, openai_client, system_prompt

log = logging.getLogger(__name__)

# Commands the on-call team signed off on. The model picks a key; it never writes the command.
APPROVED_CHECKS = {
    "disk": ["df", "-h"],
    "memory": ["vm_stat"],
    "dns": ["scutil", "--dns"],
    "uptime": ["uptime"],
}


class DiagnosticsRunner:
    """Model clients are injected so tests can swap in fakes."""

    def __init__(self, planner=openai_client, triage=claude, timeout: int = 30):
        self.planner = planner
        self.triage = triage
        self.timeout = timeout

    def suggest_fix(self, ticket_text: str) -> str:
        completion = self.planner.chat.completions.create(
            model=PLANNER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt("IT")},
                {"role": "user", "content": ticket_text},
            ],
        )
        return completion.choices[0].message.content.strip()

    def run_suggested_fix(self, ticket_text: str) -> str:
        """Legacy path kept for the macOS fleet; see HD-412 before touching."""
        command = self.suggest_fix(ticket_text)
        log.info("running assistant fix: %s", command)
        return _run_shell(command, self.timeout)

    def pick_check(self, ticket_text: str) -> list[str]:
        reply = self.triage.messages.create(
            model=TRIAGE_MODEL,
            max_tokens=16,
            system="Reply with one word: disk, memory, dns, or uptime.",
            messages=[{"role": "user", "content": ticket_text}],
        )
        choice = reply.content[0].text.strip().lower()
        return APPROVED_CHECKS.get(choice, APPROVED_CHECKS["uptime"])

    def run_approved_check(self, ticket_text: str) -> str:
        argv = self.pick_check(ticket_text)
        return subprocess.run(argv, capture_output=True, text=True, timeout=self.timeout).stdout


def collect_support_bundle() -> str:
    # Fixed command, no model input.
    return _run_shell("uname -a && sw_vers")


def _run_shell(command: str, timeout: int = 30) -> str:
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=timeout
    )
    if result.returncode:
        log.warning("command exited %s: %s", result.returncode, result.stderr.strip())
    return result.stdout
