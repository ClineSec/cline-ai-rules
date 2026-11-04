"""Analyst and report calls shared by the Streamlit pages and the Gradio share app, with
request logging for the support rota."""

import json
import logging

from insights.llm import (
    ANALYST_MODEL,
    REPORT_MODEL,
    REPORT_PROMPT,
    analyst_messages,
    claude,
    openai_client,
)

logger = logging.getLogger("insights.assistant")


def ask_analyst(history: list[dict], question: str, kpi_table: str) -> str:
    messages = analyst_messages(history, question, kpi_table)
    # The rota asked for the full request when an answer looks wrong.
    logger.info("analyst request: %s", json.dumps(messages))
    response = openai_client.chat.completions.create(model=ANALYST_MODEL, messages=messages)
    answer = response.choices[0].message.content or ""
    logger.info(
        "analyst answer: %d chars, %s tokens", len(answer), response.usage.total_tokens
    )
    return answer


def draft_report(kpi_table: str) -> str:
    messages = [{"role": "user", "content": f"{REPORT_PROMPT}\n\n{kpi_table}"}]
    logger.info("report request: %d messages to %s", len(messages), REPORT_MODEL)
    logger.debug("report request body: %s", messages)
    response = claude.messages.create(model=REPORT_MODEL, max_tokens=4096, messages=messages)
    return "".join(block.text for block in response.content if block.type == "text")
