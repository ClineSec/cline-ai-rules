"""Replays last week's tickets through the triage agent before a release (`make e2e-replay`).

Not a test: it runs against the staging helpdesk and writes its report to reports/replay/.
"""

from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, PermissionResultAllow


async def _no_prompts(tool_name, tool_input, context):
    # The replay runs unattended, so nobody is there to answer a prompt.
    return PermissionResultAllow()


def replay_options(workdir: Path) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(cwd=str(workdir), can_use_tool=_no_prompts, max_turns=30)


async def replay(workdir: Path, ticket_ids: list[str]) -> None:
    async with ClaudeSDKClient(options=replay_options(workdir)) as client:
        for ticket_id in ticket_ids:
            await client.query(f"Triage ticket {ticket_id} from the staging export in exports/.")
            async for _ in client.receive_response():
                pass
