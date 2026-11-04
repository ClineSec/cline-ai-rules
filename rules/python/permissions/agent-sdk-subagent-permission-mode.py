import dataclasses

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions
from claude_agent_sdk import types as sdk_types

FIXER_MODE = "acceptEdits"

FIXER = AgentDefinition(
    description="Fixes lint errors",
    prompt="Fix the lint errors in the files you are given.",
    tools=["Read", "Edit", "Bash"],
    # ruleid: agent-sdk-subagent-permission-mode
    permissionMode=FIXER_MODE,
)

OPTIONS = ClaudeAgentOptions(
    permission_mode="dontAsk",
    allowed_tools=["Read", "Grep"],
    agents={
        "fixer": FIXER,
        "triager": AgentDefinition(
            description="Labels new issues",
            prompt="Read the issue and pick labels.",
            # ruleid: agent-sdk-subagent-permission-mode
            permissionMode="auto",
        ),
        "planner": AgentDefinition(
            description="Plans a refactor",
            prompt="Plan the refactor without editing.",
            # ok: agent-sdk-subagent-permission-mode
            permissionMode="plan",
        ),
        "reader": sdk_types.AgentDefinition(
            description="Answers questions about the code",
            prompt="Answer from the code only.",
            # ok: agent-sdk-subagent-permission-mode
            permissionMode="dontAsk",
        ),
        # Current SDKs ignore bypassPermissions on a subagent.
        "legacy": AgentDefinition(
            description="Old release helper",
            prompt="Cut the release.",
            # ok: agent-sdk-subagent-permission-mode
            permissionMode="bypassPermissions",
        ),
    },
)

# ruleid: agent-sdk-subagent-permission-mode
NIGHTLY_FIXER = dataclasses.replace(FIXER, permissionMode="auto", maxTurns=40)

# The session's own mode is not a subagent's.
# ok: agent-sdk-subagent-permission-mode
EDIT_SESSION = ClaudeAgentOptions(permission_mode="acceptEdits", allowed_tools=["Read", "Edit"])


def reviewer(mode: str) -> AgentDefinition:
    # A run-time value can't be read here.
    # ok: agent-sdk-subagent-permission-mode
    return AgentDefinition(description="Reviews diffs", prompt="Review the diff.", permissionMode=mode)


def clamp(requested: str) -> AgentDefinition:
    return AgentDefinition(
        description="Reviews diffs",
        prompt="Review the diff.",
        # ok: agent-sdk-subagent-permission-mode
        permissionMode="default" if requested == "auto" else requested,
    )
