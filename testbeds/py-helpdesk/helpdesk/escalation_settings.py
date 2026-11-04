"""Settings for escalations: Jira for stuck tickets, the status page, and the on-call dashboards."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class EscalationSettings:
    model: str = os.environ.get("HELPDESK_ESCALATION_MODEL", "claude-sonnet-5-5")
    jira_base_url: str = os.environ.get("HELPDESK_JIRA_URL", "https://jira.example.com")
    jira_project: str = os.environ.get("HELPDESK_JIRA_PROJECT", "OPS")
    jira_api_token: str = os.environ.get("HELPDESK_JIRA_API_TOKEN", "")
    status_page_url: str = "https://status.example.com/api/v2/summary.json"
    status_page_user: str = "helpdesk"
    status_page_password: str = os.environ.get("HELPDESK_STATUS_PAGE_PASSWORD", "")
    max_tokens: int = int(os.environ.get("HELPDESK_ESCALATION_MAX_TOKENS", "1024"))


ESCALATION = EscalationSettings()
