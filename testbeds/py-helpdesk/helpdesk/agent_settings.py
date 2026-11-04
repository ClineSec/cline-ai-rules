"""Settings for the Claude Agent SDK jobs: nightly triage and the KB refresh."""

import os
from dataclasses import dataclass, field


def _tools(*names: str) -> list[str]:
    return list(names)


@dataclass(frozen=True)
class AgentJobSettings:
    model: str = os.environ.get("HELPDESK_AGENT_MODEL", "claude-sonnet-5-5")
    max_turns: int = int(os.environ.get("HELPDESK_AGENT_MAX_TURNS", "40"))
    max_budget_usd: float = 2.0
    # The nightly job runs in a throwaway container with nobody around to approve tools.
    permission_mode: str = os.environ.get("HELPDESK_AGENT_PERMISSION_MODE", "bypassPermissions")
    allowed_tools: list[str] = field(
        default_factory=lambda: _tools("Read", "Grep", "Glob", "Bash(git log:*)")
    )
    disallowed_tools: list[str] = field(default_factory=lambda: _tools("WebFetch"))


@dataclass(frozen=True)
class ReplyDraftSettings:
    model: str = os.environ.get("HELPDESK_AGENT_MODEL", "claude-sonnet-5-5")
    # Reply drafts only read the KB; anything not on the list is refused, not prompted.
    permission_mode: str = os.environ.get("HELPDESK_REPLY_PERMISSION_MODE", "dontAsk")
    allowed_tools: list[str] = field(default_factory=lambda: _tools("Read", "Grep"))


SETTINGS = AgentJobSettings()
REPLY_SETTINGS = ReplyDraftSettings()
