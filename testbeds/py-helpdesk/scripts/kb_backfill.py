"""Backfill missing knowledge-base articles from closed tickets with Claude Code.

The session reads tickets and delegates; the kb-writer subagent writes the drafts into
kb/drafts/ for a human to review before anything is published.
"""

import json
import subprocess
import sys

KB_WRITER = {
    "kb-writer": {
        "description": "Writes a knowledge-base draft for one closed ticket.",
        "prompt": "Write a short how-to article for the ticket you are given into kb/drafts/.",
        "tools": ["Read", "Write", "Edit"],
        "permissionMode": "acceptEdits",
    }
}

KB_CHECKER = {
    "kb-checker": {
        "description": "Checks a draft against the ticket it came from.",
        "prompt": "List anything in the draft that the ticket doesn't support.",
        "tools": ["Read", "Grep"],
    }
}


def backfill(ticket_ids: list[str]) -> None:
    for ticket_id in ticket_ids:
        subprocess.run(
            [
                "claude",
                "-p",
                f"Read ticket {ticket_id} from exports/closed/ and have kb-writer draft an article.",
                "--allowedTools",
                "Read",
                "Agent",
                "--agents",
                json.dumps(KB_WRITER),
            ],
            check=True,
        )


def check(ticket_id: str) -> None:
    subprocess.run(
        ["claude", "-p", f"Check the draft for ticket {ticket_id}.", "--agents", json.dumps(KB_CHECKER)],
        check=True,
    )


if __name__ == "__main__":
    backfill(sys.argv[1:])
