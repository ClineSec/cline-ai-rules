"""Release-note drafts for the helpdesk changelog, written by Cline CLI from the git log.

Runs from the release job on the build host; ops can point cline_bin at a pinned install.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class ReleaseNotesAgent:
    def __init__(self, repo: Path, cline_bin: str = "cline", timeout: int = 600) -> None:
        self.repo = repo
        self.cline_bin = cline_bin
        self.timeout = timeout

    def _run(self, *args: str) -> str:
        done = subprocess.run(
            [self.cline_bin, "--json", "--cwd", str(self.repo), *args],
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        done.check_returncode()
        return done.stdout

    def draft(self, since_tag: str) -> str:
        return self._run(f"Draft changelog entries for the commits since {since_tag} into CHANGELOG.md")

    def list_tickets(self, since_tag: str) -> str:
        # Plan mode reads and answers; it doesn't edit files or run commands.
        done = subprocess.run(
            [self.cline_bin, "--plan", "--json", "--cwd", str(self.repo),
             f"List the ticket numbers in the commits since {since_tag}"],
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        return done.stdout
