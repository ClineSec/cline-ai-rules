"""Escalation assistant: turns a stuck ticket into a Jira issue for the on-call team."""

import httpx

from .escalation_settings import ESCALATION
from .llm import claude

# The model files the issue itself through this tool; the service just relays the request.
HTTP_TOOL = {
    "name": "http_request",
    "description": "Send an HTTP request and return the response body.",
    "input_schema": {
        "type": "object",
        "properties": {
            "method": {"type": "string"},
            "url": {"type": "string"},
            "headers": {"type": "object"},
            "body": {"type": "string"},
        },
        "required": ["method", "url"],
    },
}


def _escalation_prompt(team: str) -> str:
    return (
        f"You escalate {team} helpdesk tickets that nobody has picked up in 4 hours. "
        f"Create an issue in the {ESCALATION.jira_project} project at {ESCALATION.jira_base_url}/rest/api/3/issue "
        f"with the http_request tool, sending 'Authorization: Bearer {ESCALATION.jira_api_token}'. "
        "Summarize the ticket in the issue body and reply with the issue key."
    )


def _status_summary() -> str:
    resp = httpx.get(
        ESCALATION.status_page_url,
        auth=(ESCALATION.status_page_user, ESCALATION.status_page_password),
        timeout=10,
    )
    components = resp.json()["components"]
    return ", ".join(f"{c['name']}: {c['status']}" for c in components)


def escalate(ticket_text: str, team: str = "IT"):
    return claude.messages.create(
        model=ESCALATION.model,
        max_tokens=ESCALATION.max_tokens,
        system=_escalation_prompt(team),
        messages=[{"role": "user", "content": ticket_text}],
        tools=[HTTP_TOOL],
    )


def status_reply(question: str):
    # The password logs in to the status page here; the model only sees what the page reports.
    return claude.messages.create(
        model=ESCALATION.model,
        max_tokens=ESCALATION.max_tokens,
        system=f"Current service status: {_status_summary()}. Answer questions about outages from it.",
        messages=[{"role": "user", "content": question}],
    )
