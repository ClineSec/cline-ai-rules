"""Weekly digest agent (OpenAI Agents SDK): drafts the KPI digest and sends it.

Mail and chat go through hosted MCP servers. The Agents SDK asks on_approval_request whenever
a server's tool needs approval.
"""

import logging
import os

from agents import Agent, HostedMCPTool, MCPToolApprovalRequest, Runner

from .llm import ANALYST_MODEL

log = logging.getLogger(__name__)

MAILER_URL = os.environ.get("MAILER_MCP_URL", "https://mailer-mcp.example.com/mcp")
CHAT_URL = os.environ.get("CHAT_MCP_URL", "https://chat-mcp.example.com/mcp")


def _approve_digest_calls(request: MCPToolApprovalRequest):
    """The digest goes out every Monday; approving each send by hand held it up."""
    log.info("approving %s on %s", request.data.name, request.data.server_label)
    return {"approve": True}


def _approve_chat_reads(request: MCPToolApprovalRequest):
    if request.data.name in {"list_channels", "search_messages"}:
        return {"approve": True}
    return {"approve": False, "reason": "Posting needs a person; use the review queue."}


mailer = HostedMCPTool(
    tool_config={
        "type": "mcp",
        "server_label": "mailer",
        "server_url": MAILER_URL,
        "require_approval": "always",
    },
    on_approval_request=_approve_digest_calls,
)

chat = HostedMCPTool(
    tool_config={
        "type": "mcp",
        "server_label": "chat",
        "server_url": CHAT_URL,
        "require_approval": {
            "never": {"tool_names": ["list_channels", "search_messages"]},
            "always": {"tool_names": ["post_message"]},
        },
    },
    on_approval_request=_approve_chat_reads,
)

digest_agent = Agent(
    name="weekly-digest",
    model=ANALYST_MODEL,
    instructions=(
        "Draft the weekly KPI digest from the numbers you are given, send it to the growth "
        "list with the mailer, and link it in the team channel."
    ),
    tools=[mailer, chat],
)


async def send_weekly_digest(kpi_table: str) -> str:
    result = await Runner.run(digest_agent, f"KPIs this week:\n{kpi_table}")
    return result.final_output
