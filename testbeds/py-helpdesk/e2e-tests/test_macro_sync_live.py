"""Live checks against a throwaway workspace. Run with `pytest e2e-tests -m live` and an API key."""

import pytest
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher, PermissionResultAllow, ResultMessage

pytestmark = pytest.mark.live


async def test_permission_callback_sees_writes(tmp_path):
    seen: list[str] = []

    async def record_and_allow(tool_name, tool_input, context):
        seen.append(tool_name)
        return PermissionResultAllow()

    options = ClaudeAgentOptions(cwd=str(tmp_path), can_use_tool=record_and_allow, max_turns=3)
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Create notes.txt containing the word hello.")
        async for message in client.receive_response():
            if isinstance(message, ResultMessage):
                break
    assert "Write" in seen


async def test_pre_tool_hook_decision_is_honored(tmp_path):
    async def approve(input_data, tool_use_id, context):
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}

    options = ClaudeAgentOptions(
        cwd=str(tmp_path),
        hooks={"PreToolUse": [HookMatcher(matcher="Bash", hooks=[approve])]},
        max_turns=3,
    )
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Run `echo hello`.")
        async for message in client.receive_response():
            if isinstance(message, ResultMessage):
                assert not message.is_error
