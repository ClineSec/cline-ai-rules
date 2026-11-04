from claude_agent_sdk import ClaudeAgentOptions, query

ALLOWED_TOOLS = [
    # ok: agent-sdk-mcp-auto-approve
    "Read",
    # ok: agent-sdk-mcp-auto-approve
    "mcp__tickets__get_ticket",
    # ruleid: agent-sdk-mcp-auto-approve
    "mcp__tickets__close_ticket",
]

DISALLOWED_TOOLS = [
    # ok: agent-sdk-mcp-auto-approve
    "mcp__tickets__delete_ticket",
]


async def run(prompt: str) -> None:
    options = ClaudeAgentOptions(
        allowed_tools=[
            *ALLOWED_TOOLS,
            # ruleid: agent-sdk-mcp-auto-approve
            "mcp__github",
            # ok: agent-sdk-mcp-auto-approve
            "mcp__github__search_code",
            # ok: agent-sdk-mcp-auto-approve
            "mcp__*",
        ],
        disallowed_tools=DISALLOWED_TOOLS,
    )
    async for message in query(prompt=prompt, options=options):
        print(message)


def ops_options() -> dict:
    return {
        # ruleid: agent-sdk-mcp-auto-approve
        "allowed_tools": ["Grep", "mcp__ops__*"],
        "permission_mode": "dontAsk",
    }


YOLO = ClaudeAgentOptions(
    permission_mode="bypassPermissions",
    # ok: agent-sdk-mcp-auto-approve
    allowed_tools=["mcp__ops__*"],
)

# ok: agent-sdk-mcp-auto-approve
NOTE = "mcp__tickets__close_ticket"
