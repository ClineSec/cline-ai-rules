"""Weekly digest of vendor SDK changes that may explain new ticket types.

Reads the tickets tagged with a vendor SDK, asks Claude to fetch each vendor's changelog, and
writes a short digest to reports/vendor-digest.md for the support leads.

    uv run scripts/vendor_changelog_digest.py --since 2026-10-18
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, query

# Changelogs live on each vendor's own site, so the digest agent may fetch any page.
CHANGELOG_TOOLS: list[str] = ["Read", "Grep", "WebFetch"]
# Ticket lookups only need our own API docs.
TICKET_TOOLS: list[str] = ["Read", "Grep", "WebFetch(domain:docs.example.com)"]

REPORT = Path("reports/vendor-digest.md")


def digest_options(workdir: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=workdir,
        allowed_tools=CHANGELOG_TOOLS,
        permission_mode="default",
        max_turns=20,
    )


def ticket_options(workdir: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(cwd=workdir, allowed_tools=TICKET_TOOLS, max_turns=8)


async def build_digest(since: str, workdir: str) -> str:
    prompt = (
        f"List the vendor SDKs named in tickets closed since {since} (tickets/closed/*.json), "
        "fetch each vendor's changelog, and summarize changes that could explain the tickets."
    )
    text = ""
    async for message in query(prompt=prompt, options=digest_options(workdir)):
        if getattr(message, "result", None):
            text = message.result
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", required=True)
    parser.add_argument("--workdir", default=".")
    args = parser.parse_args()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(asyncio.run(build_digest(args.since, args.workdir)) + "\n")


if __name__ == "__main__":
    main()
