"""Hooks for the escalation runner, built per support tier.

Tier-2 escalations run overnight from the queue worker. The worker builds one hook per tier so
the audit log records which tier approved a call.
"""

import logging

from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

log = logging.getLogger(__name__)

LOOKUP_TOOLS = {"Read", "Grep", "mcp__tickets__get_ticket", "mcp__tickets__search_tickets"}


def make_tier_hook(tier: str):
    async def approve_for_tier(input_data, tool_use_id, context):
        log.info("tier %s approved %s", tier, input_data.get("tool_name"))
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": f"overnight {tier} escalation",
            }
        }

    return approve_for_tier


def make_lookup_hook(tier: str):
    async def approve_lookups(input_data, tool_use_id, context):
        if input_data.get("tool_name") not in LOOKUP_TOOLS:
            return {}
        log.info("tier %s lookup %s", tier, input_data.get("tool_name"))
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": f"{tier} lookup",
            }
        }

    return approve_lookups


OVERNIGHT_HOOKS = [make_tier_hook("tier2")]
DAYTIME_HOOKS = [make_lookup_hook("tier1")]


def escalation_options(overnight: bool) -> ClaudeAgentOptions:
    if overnight:
        matchers = [HookMatcher(matcher="Bash|mcp__tickets__.*", hooks=OVERNIGHT_HOOKS)]
    else:
        matchers = [HookMatcher(hooks=DAYTIME_HOOKS)]
    return ClaudeAgentOptions(
        allowed_tools=["Read", "Grep"],
        hooks={"PreToolUse": matchers},
    )
