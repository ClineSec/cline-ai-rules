import dataclasses
import os
from dataclasses import dataclass
from typing import Literal

from claude_agent_sdk import (
    AgentDefinition,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResultAllow,
    PermissionResultDeny,
    query,
)
from claude_code_sdk import ClaudeCodeOptions

# ruleid: agent-sdk-bypass-permissions
AGENT_MODE = "bypassPermissions"
SAFE_TOOLS = {"Read", "Grep", "Glob"}


async def fix_lint(repo: str):
    options = ClaudeAgentOptions(
        cwd=repo,
        # ruleid: agent-sdk-bypass-permissions
        permission_mode="bypassPermissions",
        max_turns=20,
    )
    async for message in query(prompt="Fix the lint errors.", options=options):
        print(message)


DANGER_MODE = "bypassPermissions"


def options_from_guard_named_constant() -> ClaudeAgentOptions:
    # ruleid: agent-sdk-bypass-permissions
    return ClaudeAgentOptions(permission_mode=DANGER_MODE)


def options_from_constant() -> ClaudeAgentOptions:
    # Reported where AGENT_MODE is assigned, not again here.
    # ok: agent-sdk-bypass-permissions
    return ClaudeAgentOptions(permission_mode=AGENT_MODE, allowed_tools=["Read", "Edit"])


def options_from_env() -> ClaudeAgentOptions:
    # ruleid: agent-sdk-bypass-permissions
    mode = os.environ.get("AGENT_PERMISSION_MODE", "bypassPermissions")
    return ClaudeAgentOptions(permission_mode=mode)


def options_for_ci(ci: bool) -> ClaudeAgentOptions:
    # ruleid: agent-sdk-bypass-permissions
    return ClaudeAgentOptions(permission_mode="bypassPermissions" if ci else "default")


def legacy_options() -> ClaudeCodeOptions:
    # ruleid: agent-sdk-bypass-permissions
    return ClaudeCodeOptions(permission_mode="bypassPermissions")


def widen(base: ClaudeAgentOptions) -> ClaudeAgentOptions:
    # ruleid: agent-sdk-bypass-permissions
    return dataclasses.replace(base, permission_mode="bypassPermissions")


# ruleid: agent-sdk-bypass-permissions
def build_options(repo: str, permission_mode: str = "bypassPermissions") -> ClaudeAgentOptions:
    return ClaudeAgentOptions(cwd=repo, permission_mode=permission_mode)


AGENT_DEFAULTS = {
    "max_turns": 30,
    # ruleid: agent-sdk-bypass-permissions
    "permission_mode": "bypassPermissions",
}


@dataclass
class AgentSettings:
    model: str = "claude-sonnet-5-5"
    # ruleid: agent-sdk-bypass-permissions
    permission_mode: str = os.getenv("TRIAGE_PERMISSION_MODE", "bypassPermissions")


def mutate(options: ClaudeAgentOptions) -> None:
    # ruleid: agent-sdk-bypass-permissions
    options.permission_mode = "bypassPermissions"


async def escalate(client: ClaudeSDKClient) -> None:
    await client.query("Review the plan first.")
    # ruleid: agent-sdk-bypass-permissions
    await client.set_permission_mode("bypassPermissions")


def skip_flag() -> ClaudeAgentOptions:
    # ruleid: agent-sdk-bypass-permissions
    return ClaudeAgentOptions(extra_args={"dangerously-skip-permissions": None})


def cli_mode_flag() -> ClaudeAgentOptions:
    # ruleid: agent-sdk-bypass-permissions
    return ClaudeAgentOptions(extra_args={"permission-mode": "bypassPermissions"})


async def nightly(ticket_id: str):
    # ruleid: agent-sdk-bypass-permissions
    return await run_agent_job(ticket_id, mode="bypassPermissions")


def from_settings(settings) -> ClaudeAgentOptions:
    # Reported where the settings field is assigned.
    # ok: agent-sdk-bypass-permissions
    return ClaudeAgentOptions(permission_mode=settings.permission_mode)


def settings_json() -> ClaudeAgentOptions:
    import json

    # ruleid: agent-sdk-bypass-permissions
    return ClaudeAgentOptions(settings=json.dumps({"permissions": {"defaultMode": "bypassPermissions"}}))


async def approve_everything(tool_name, tool_input, context):
    return PermissionResultAllow(updated_input=tool_input)


async def approve_and_log(tool_name, tool_input, context):
    print("tool", tool_name)
    return PermissionResultAllow()


# ruleid: agent-sdk-bypass-permissions
ALWAYS = ClaudeAgentOptions(can_use_tool=approve_everything)
# ruleid: agent-sdk-bypass-permissions
LOGGED = ClaudeAgentOptions(can_use_tool=approve_and_log)


# --- near misses ---------------------------------------------------------------------

# ok: agent-sdk-bypass-permissions
READ_ONLY = ClaudeAgentOptions(permission_mode="default", allowed_tools=["Read", "Grep"], max_turns=20)
# ok: agent-sdk-bypass-permissions
EDITS = ClaudeAgentOptions(permission_mode="acceptEdits", allowed_tools=["Read", "Edit"])
# ok: agent-sdk-bypass-permissions
PLANNING = ClaudeAgentOptions(permission_mode="plan")
# ok: agent-sdk-bypass-permissions
HEADLESS = ClaudeAgentOptions(permission_mode="dontAsk", allowed_tools=["Read", "Bash(npm test)"])
# ok: agent-sdk-bypass-permissions
FROM_ENV = ClaudeAgentOptions(permission_mode=os.environ.get("AGENT_PERMISSION_MODE", "default"))


def clamp(requested: str) -> ClaudeAgentOptions:
    # ok: agent-sdk-bypass-permissions
    return ClaudeAgentOptions(permission_mode="default" if requested == "bypassPermissions" else requested)


# A constant named for the danger is a guard, and its use below is a comparison.
# ok: agent-sdk-bypass-permissions
UNSAFE_MODE = "bypassPermissions"


def refuse_bypass(options: ClaudeAgentOptions) -> None:
    # ok: agent-sdk-bypass-permissions
    if options.permission_mode == UNSAFE_MODE:
        raise ValueError("unsafe mode")
    # ok: agent-sdk-bypass-permissions
    if options.permission_mode == "bypassPermissions":
        raise ValueError("bypassPermissions is not allowed for ticket-driven runs")
    # ok: agent-sdk-bypass-permissions
    print("permission mode is not bypassPermissions")


# ok: agent-sdk-bypass-permissions
PermissionMode = Literal["default", "acceptEdits", "plan", "bypassPermissions", "dontAsk", "auto"]

# A different library with its own permission_mode keyword.
# ok: agent-sdk-bypass-permissions
upload = storage.put_object("report.csv", permission_mode="private")


# Claude Code never applies bypassPermissions from a subagent definition.
WITH_REVIEWER = ClaudeAgentOptions(
    agents={
        "reviewer": AgentDefinition(
            description="Reviews diffs",
            prompt="Review the diff.",
            # ok: agent-sdk-bypass-permissions
            permissionMode="bypassPermissions",
        )
    }
)


async def gate(tool_name, tool_input, context):
    if tool_name in SAFE_TOOLS:
        return PermissionResultAllow()
    return PermissionResultDeny(message=f"{tool_name} needs a human")


async def gate_with_fallback(tool_name, tool_input, context):
    try:
        policy.check(tool_name, tool_input)
    except PermissionError as exc:
        return PermissionResultDeny(message=str(exc))
    return PermissionResultAllow()


# ok: agent-sdk-bypass-permissions
GATED = ClaudeAgentOptions(can_use_tool=gate, permission_mode="default")
# ok: agent-sdk-bypass-permissions
GATED_FALLBACK = ClaudeAgentOptions(can_use_tool=gate_with_fallback)
# ok: agent-sdk-bypass-permissions
SANDBOX_FLAG = ClaudeAgentOptions(extra_args={"debug-to-stderr": None})


class RunnerSettings(BaseModel):
    # A list of accepted modes lists bypass as a choice; it sets nothing.
    # ok: agent-sdk-bypass-permissions
    allowed_permission_mode: list[str] = ["default", "plan", "bypassPermissions"]
    # ok: agent-sdk-bypass-permissions
    permission_mode: str = Field("default", json_schema_extra={"permission_mode": ["default", "bypassPermissions"]})
