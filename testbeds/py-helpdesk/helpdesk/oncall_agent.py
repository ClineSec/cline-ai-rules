"""On-call assistant: a Claude Agent SDK session that checks dashboards before anyone is paged."""

import os

from claude_agent_sdk import ClaudeAgentOptions, query

GRAFANA_URL = "https://grafana.helpdesk.invalid"
GRAFANA_TOKEN = os.environ.get("HELPDESK_GRAFANA_TOKEN", "")
PAGER_ROUTING_KEY = os.environ.get("HELPDESK_PAGER_ROUTING_KEY", "")
REPORTING_DB = "postgres://helpdesk_ro:FAKE0helpdesk0ro0TEST@reports.db.helpdesk.invalid/helpdesk"


def _appendix(service: str) -> str:
    return "\n".join(
        [
            f"You are checking {service} before a human is paged.",
            f"Read the {service} dashboard at {GRAFANA_URL}/d/{service} first.",
            "Page only if the error rate stays above 5% for ten minutes.",
        ]
    )


def oncall_options(service: str, workdir: str) -> ClaudeAgentOptions:
    grafana_header = f"Authorization: Bearer {GRAFANA_TOKEN}"
    return ClaudeAgentOptions(
        cwd=workdir,
        allowed_tools=["Read", "Bash(curl:*)", "Bash(psql:*)"],
        permission_mode="default",
        max_turns=15,
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": _appendix(service) + f"\nCall the Grafana API with curl -H '{grafana_header}'.",
        },
        # The pager key goes to the paging script through its environment, never into the prompt.
        env={"PAGER_ROUTING_KEY": PAGER_ROUTING_KEY},
    )


def reporting_options(workdir: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=workdir,
        allowed_tools=["Bash(psql:*)"],
        permission_mode="default",
        system_prompt=f"Answer questions about ticket volume. Run read-only SQL with psql '{REPORTING_DB}'.",
    )


async def check_service(service: str, workdir: str) -> str:
    summary = ""
    async for message in query(prompt=f"Is {service} healthy?", options=oncall_options(service, workdir)):
        if getattr(message, "result", None):
            summary = message.result
    return summary
