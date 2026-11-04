"""Model clients and prompts shared by the dashboard pages."""

import os

from anthropic import Anthropic
from google import genai
from openai import OpenAI

ANALYST_MODEL = os.environ.get("INSIGHTS_ANALYST_MODEL", "gpt-5")
REPORT_MODEL = os.environ.get("INSIGHTS_REPORT_MODEL", "claude-sonnet-5-5")
ANOMALY_MODEL = os.environ.get("INSIGHTS_ANOMALY_MODEL", "gemini-3-pro")

openai_client = OpenAI()
claude = Anthropic()
gemini = genai.Client()

ANALYST_PROMPT = (
    "You are the analytics assistant for the growth team. Answer questions about the KPI "
    "table you are given. Keep answers short. You may use simple HTML (<b>, <ul>, <table>) "
    "for emphasis."
)

REPORT_PROMPT = (
    "Write the weekly growth report as a single self-contained HTML document with inline CSS. "
    "Use the KPI table below; call out the three biggest changes."
)


def analyst_messages(history: list[dict], question: str, kpi_table: str) -> list[dict]:
    """Chat Completions messages for one assistant turn."""
    return [
        {"role": "system", "content": f"{ANALYST_PROMPT}\n\nKPIs:\n{kpi_table}"},
        *({"role": turn["role"], "content": turn["content"]} for turn in history),
        {"role": "user", "content": question},
    ]
