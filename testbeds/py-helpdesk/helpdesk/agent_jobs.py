"""Hand a ticket to a coding agent CLI on the helpdesk host and collect its summary.

Support engineers pick the agent per team in HELPDESK_AGENT. Unattended runs come from the
queue worker, so they cannot stop for approval prompts.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field

CLAUDE_BIN = shutil.which("claude") or "/opt/helpdesk/bin/claude"

# argv templates; "{prompt}" is filled in by build_argv().
AGENT_ARGV: dict[str, tuple[str, ...]] = {
    "claude": (CLAUDE_BIN, "-p", "{prompt}", "--output-format", "json",
               "--permission-mode", "bypassPermissions"),
    "codex": ("codex", "exec", "--sandbox", "workspace-write", "{prompt}"),
    "gemini": ("gemini", "--approval-mode", "auto_edit", "-p", "{prompt}"),
}

# Queue-worker runs have nobody to answer prompts. Each entry replaces the template's own
# approval flags (the slice) with the agent's unattended flags.
UNATTENDED: dict[str, tuple[slice, tuple[str, ...]]] = {
    "codex": (slice(2, 4), ("--dangerously-bypass-approvals-and-sandbox",)),
    "gemini": (slice(1, 3), ("--approval-mode", "yolo")),
}

# Flags a support engineer may not pass through HELPDESK_AGENT_EXTRA_ARGS.
FORBIDDEN_FLAGS = frozenset({"--dangerously-skip-permissions", "--yolo", "--allow-all-tools"})


@dataclass
class AgentJob:
    agent: str
    prompt: str
    unattended: bool = False
    extra_args: list[str] = field(default_factory=list)

    def build_argv(self) -> list[str]:
        argv = [part.format(prompt=self.prompt) for part in AGENT_ARGV[self.agent]]
        if self.unattended and self.agent in UNATTENDED:
            drop, flags = UNATTENDED[self.agent]
            argv[drop] = flags
        bad = FORBIDDEN_FLAGS.intersection(self.extra_args)
        if bad:
            raise ValueError(f"flags not allowed: {sorted(bad)}")
        return argv + self.extra_args


class CopilotRunner:
    """Runs GitHub Copilot CLI for teams that standardized on it."""

    def __init__(self, workdir: str) -> None:
        self.workdir = workdir

    def env(self) -> dict[str, str]:
        return {**os.environ, "COPILOT_ALLOW_ALL": "yes", "NO_COLOR": "1"}

    def summarize(self, prompt: str) -> str:
        done = subprocess.run(
            ["copilot", "-p", prompt, "--no-color"],
            cwd=self.workdir,
            env=self.env(),
            capture_output=True,
            text=True,
            timeout=600,
        )
        return done.stdout


def run(job: AgentJob) -> str:
    done = subprocess.run(job.build_argv(), capture_output=True, text=True, timeout=900)
    return done.stdout


def from_env(prompt: str) -> AgentJob:
    return AgentJob(
        agent=os.environ.get("HELPDESK_AGENT", "codex"),
        prompt=prompt,
        unattended=os.environ.get("HELPDESK_UNATTENDED") == "1",
        extra_args=os.environ.get("HELPDESK_AGENT_EXTRA_ARGS", "").split(),
    )
