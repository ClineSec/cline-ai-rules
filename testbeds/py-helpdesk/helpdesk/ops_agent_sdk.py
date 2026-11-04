"""Claude Agent SDK runner for the on-call ops assistant.

It reads service status from the ops MCP server and, for the restart runbook, restarts a
stuck worker. Status page updates are drafted for a human to post.
"""

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

OPS_SERVERS = {
    "ops": {"type": "http", "url": "https://ops-mcp.example.invalid/mcp"},
    "statuspage": {"type": "http", "url": "https://statuspage-mcp.example.invalid/mcp"},
}

# Status checks never need a prompt.
OPS_READ_TOOLS = ["Read", "mcp__ops__get_service_status", "mcp__ops__list_workers"]

# The restart runbook may restart a worker on its own (approved in INC-2291).
RESTART_ALLOWED_TOOLS = [*OPS_READ_TOOLS, "mcp__ops__restart_worker"]

STATUS_PROMPT = "Summarize the health of every helpdesk service and list workers stuck for 10+ minutes."
RESTART_PROMPT = "Follow docs/runbooks/stuck-worker.md for each stuck worker."


def _options(allowed: list[str]) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        mcp_servers=OPS_SERVERS,
        allowed_tools=allowed,
        permission_mode="dontAsk",
        max_turns=12,
    )


async def _run(prompt: str, options: ClaudeAgentOptions) -> str:
    summary = ""
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage) and message.result:
            summary = message.result
    return summary


async def status_report() -> str:
    return await _run(STATUS_PROMPT, _options(OPS_READ_TOOLS))


async def restart_stuck_workers() -> str:
    return await _run(RESTART_PROMPT, _options(RESTART_ALLOWED_TOOLS))


async def status_update_draft() -> str:
    options = ClaudeAgentOptions(
        mcp_servers=OPS_SERVERS,
        allowed_tools=[*OPS_READ_TOOLS, "mcp__statuspage"],
        permission_mode="dontAsk",
    )
    return await _run("Draft a status page update for the current incident.", options)
