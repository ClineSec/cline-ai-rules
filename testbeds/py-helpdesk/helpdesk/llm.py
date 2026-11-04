"""Model clients shared by the helpdesk services."""

import os

import anthropic
from openai import OpenAI

PLANNER_MODEL = os.environ.get("HELPDESK_PLANNER_MODEL", "gpt-5")
TRIAGE_MODEL = os.environ.get("HELPDESK_TRIAGE_MODEL", "claude-sonnet-5-5")

openai_client = OpenAI()
claude = anthropic.Anthropic()
claude_async = anthropic.AsyncAnthropic()


def system_prompt(team: str) -> str:
    return (
        f"You are the {team} helpdesk assistant. Answer briefly. "
        "When a fix needs a command, reply with only the command."
    )
