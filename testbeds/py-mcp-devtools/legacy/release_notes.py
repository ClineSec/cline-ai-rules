"""Release-note drafting on MCP Python SDK 1.x, for the clients still on the legacy server.

Asks the client's model through `ctx.session.create_message` (server-initiated sampling,
which 1.x clients support). Commit lists come from git; the model only rewrites them.
"""

import os
import subprocess

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import SamplingMessage, TextContent

mcp = FastMCP("devtools-release-notes")

REPO_ROOT = os.environ.get("DEVTOOLS_REPO", "/srv/checkout")

# Shared by every drafting tool; a tool can override any of these per call.
HOST_SAMPLING = dict(
    max_tokens=800,
    temperature=0.2,
    include_context="allServers",
)


async def ask_host(ctx: Context, prompt: str, **overrides) -> str:
    result = await ctx.session.create_message(
        messages=[SamplingMessage(role="user", content=TextContent(type="text", text=prompt))],
        **{**HOST_SAMPLING, **overrides},
    )
    return result.content.text if result.content.type == "text" else ""


def _commits(since: str) -> str:
    return subprocess.run(
        ["git", "log", "--oneline", "--no-merges", "--end-of-options", f"{since}..HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    ).stdout


@mcp.tool()
async def draft_release_notes(since_tag: str, ctx: Context) -> str:
    """Draft user-facing release notes for the commits since a tag."""
    return await ask_host(ctx, f"Group these commits into Added / Fixed / Changed:\n\n{_commits(since_tag)}")


@mcp.tool()
async def release_title(since_tag: str, ctx: Context) -> str:
    """A short title for the release."""
    # The title only needs the commit list.
    return await ask_host(ctx, f"One short release title for:\n{_commits(since_tag)}", include_context="none", max_tokens=30)


if __name__ == "__main__":
    mcp.run()
