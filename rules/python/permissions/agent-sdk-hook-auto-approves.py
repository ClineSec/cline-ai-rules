import logging

import claude_agent_sdk
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher, query
from claude_agent_sdk.types import PreToolUseHookSpecificOutput, SyncHookJSONOutput

log = logging.getLogger(__name__)

READ_ONLY_TOOLS = {"Read", "Glob", "Grep"}
SHELL_MATCHER = "Bash"
READ_ONLY_MATCHER = "Read|Glob|Grep"

ALLOW = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}


async def approve_everything(input_data, tool_use_id, context):
    log.info("tool call %s", input_data.get("tool_name"))
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "unattended run",
        }
    }


async def approve_after_event_guard(input_data, tool_use_id, context):
    if input_data["hook_event_name"] != "PreToolUse":
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": input_data["hook_event_name"],
            "permissionDecision": "allow",
        }
    }


async def approve_constant(input_data, tool_use_id, context):
    return ALLOW


async def grant_permission_request(input_data, tool_use_id, context):
    return {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {"behavior": "allow"},
        }
    }


async def legacy_approve(input_data, tool_use_id, context):
    return {"decision": "approve", "reason": "trusted job"}


async def typed_allow(input_data, tool_use_id, context) -> SyncHookJSONOutput:
    return SyncHookJSONOutput(
        hookSpecificOutput=PreToolUseHookSpecificOutput(
            hookEventName="PreToolUse", permissionDecision="allow"
        )
    )


async def approve_shell_by_name(input_data, tool_use_id, context):
    tool = input_data["tool_name"]
    if tool == "Read":
        return {}
    if tool in ("Bash", "Write"):
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}
    return {}


async def approve_all_but_notebooks(input_data, tool_use_id, context):
    if input_data["tool_name"] == "NotebookEdit":
        return {}
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}


async def approve_reads_by_name(input_data, tool_use_id, context):
    if input_data["tool_name"] in {"Read", "Grep", "mcp__tickets__list_tickets"}:
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}
    if input_data["tool_name"] == "Bash":
        log.info("shell call")
    return {}


async def approve_unless_listed(input_data, tool_use_id, context):
    if input_data["tool_name"] not in ("Read", "Grep"):
        return {}
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}


def _decision(decision: str, reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }


async def approve_via_helper(input_data, tool_use_id, context):
    return _decision("allow", "batch job")


async def gate_via_helper(input_data, tool_use_id, context):
    if input_data["tool_input"].get("file_path", "").startswith("/srv/kb/"):
        return _decision("allow", "inside the knowledge base")
    return _decision("ask", "outside the knowledge base")


async def approve_read_only(input_data, tool_use_id, context):
    if input_data["tool_name"] in READ_ONLY_TOOLS:
        return ALLOW
    return {}


async def gate_shell(input_data, tool_use_id, context):
    command = input_data["tool_input"].get("command", "")
    if command.startswith(("git status", "git diff", "npm test")):
        return ALLOW
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": "not on the allowlist",
        }
    }


async def approve_after_policy(input_data, tool_use_id, context):
    await policy_engine.enforce(input_data["tool_name"], input_data["tool_input"])
    return ALLOW


async def approve_by_ternary(input_data, tool_use_id, context):
    decision = "allow" if input_data["tool_name"] in READ_ONLY_TOOLS else "ask"
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision}}


async def audit_log(input_data, tool_use_id, context):
    log.info("tool call %s", input_data.get("tool_name"))
    return {}


class NightlyRunner:
    async def _approve(self, input_data, tool_use_id, context):
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}

    async def _approve_reads(self, input_data, tool_use_id, context):
        if input_data["tool_name"] in READ_ONLY_TOOLS:
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}
        return {}

    def options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            hooks={
                "PreToolUse": [
                    # ruleid: agent-sdk-hook-auto-approves
                    HookMatcher(matcher="Bash", hooks=[self._approve]),
                    # ok: agent-sdk-hook-auto-approves
                    HookMatcher(hooks=[self._approve_reads]),
                ]
            }
        )


def unattended_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        hooks={
            "PreToolUse": [
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(hooks=[approve_everything]),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(matcher="*", hooks=[approve_after_event_guard]),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(matcher=SHELL_MATCHER, hooks=[approve_constant]),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher("Write|Edit", [legacy_approve]),
                # ruleid: agent-sdk-hook-auto-approves
                claude_agent_sdk.HookMatcher(matcher="mcp__.*", hooks=[typed_allow]),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(matcher="Read|WebFetch", hooks=[approve_constant]),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(matcher=None, hooks=[audit_log, approve_constant], timeout=30),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(hooks=[approve_shell_by_name]),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(hooks=[approve_all_but_notebooks]),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(matcher="Bash", hooks=[approve_via_helper]),
            ],
            "PermissionRequest": [
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(matcher="", hooks=[grant_permission_request]),
            ],
        },
    )


def gated_options(matcher_from_config: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        hooks={
            "PreToolUse": [
                # The documented read-only auto-approve: the matcher only reaches Read, Glob, Grep.
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(matcher=READ_ONLY_MATCHER, hooks=[approve_constant]),
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(matcher="^(Read|Grep)$", hooks=[approve_everything]),
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(matcher="mcp__tickets__get_ticket, Glob", hooks=[approve_everything]),
                # The callback itself decides.
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(hooks=[approve_read_only]),
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(hooks=[approve_reads_by_name]),
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(hooks=[approve_unless_listed]),
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(matcher="Write|Edit", hooks=[gate_via_helper]),
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(matcher="Bash", hooks=[gate_shell]),
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(hooks=[approve_after_policy]),
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(hooks=[approve_by_ternary]),
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(hooks=[audit_log]),
                # A matcher read from configuration can't be judged here.
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(matcher=matcher_from_config, hooks=[approve_everything]),
            ],
        },
    )


def bypass_options() -> ClaudeAgentOptions:
    # Reported by agent-sdk-bypass-permissions.
    return ClaudeAgentOptions(
        permission_mode="bypassPermissions",
        # ok: agent-sdk-hook-auto-approves
        hooks={"PreToolUse": [HookMatcher(hooks=[approve_everything])]},
    )


async def run(prompt: str):
    async with ClaudeSDKClient(options=unattended_options()) as client:
        await client.query(prompt)


# Callbacks registered through a list, a partial, or a factory.
from functools import partial  # noqa: E402
import functools  # noqa: E402


async def approve_for_job(input_data, tool_use_id, context, *, job):
    log.info("job %s runs %s", job, input_data.get("tool_name"))
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}


def make_approver(reason: str):
    async def approve(input_data, tool_use_id, context):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": reason,
            }
        }

    return approve


def make_constant_approver():
    async def approve(input_data, tool_use_id, context):
        return ALLOW

    return approve


def make_reads_approver():
    async def approve(input_data, tool_use_id, context):
        if input_data["tool_name"] in READ_ONLY_TOOLS:
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}
        return {}

    return approve


APPROVERS = [audit_log, approve_everything]
FACTORY_APPROVERS: list = [make_approver("batch")]
CHECKED = [approve_read_only]


class BatchRunner:
    def __init__(self, job: str):
        self.job = job

    def _make_hook(self):
        async def hook(input_data, tool_use_id, context):
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}

        return hook

    def options(self) -> ClaudeAgentOptions:
        hooks = {
            "PreToolUse": [
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(matcher="Bash", hooks=APPROVERS),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(hooks=FACTORY_APPROVERS),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(SHELL_MATCHER, APPROVERS),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(matcher="Write|Edit", hooks=[partial(approve_for_job, job=self.job)]),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(hooks=[functools.partial(approve_for_job, job=self.job)]),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(matcher="Bash", hooks=[make_approver("nightly")]),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(matcher="mcp__.*", hooks=[make_constant_approver()]),
                # ruleid: agent-sdk-hook-auto-approves
                HookMatcher(hooks=[self._make_hook()]),
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(matcher=READ_ONLY_MATCHER, hooks=APPROVERS),
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(hooks=CHECKED),
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(hooks=[make_reads_approver()]),
                # ok: agent-sdk-hook-auto-approves
                HookMatcher(matcher="Read|Grep", hooks=[make_approver("reads")]),
            ],
        }
        # A hooks dict built first and passed later.
        return ClaudeAgentOptions(hooks=hooks)


# A matcher kept in a variable and listed later.
# ruleid: agent-sdk-hook-auto-approves
SHELL_HOOK = HookMatcher(matcher="Bash", hooks=[approve_everything])
SHELL_OPTIONS = ClaudeAgentOptions(hooks={"PreToolUse": [SHELL_HOOK]})
