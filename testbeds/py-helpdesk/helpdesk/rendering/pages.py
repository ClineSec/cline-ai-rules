"""Agent-facing HTML pages: ticket summaries and reply previews.

Mounted under /ui by helpdesk/api.py.
"""

import markdown
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from pydantic import BaseModel

from ..llm import PLANNER_MODEL, TRIAGE_MODEL, claude, openai_client, system_prompt

router = APIRouter(prefix="/ui", tags=["ui"])
templates = Jinja2Templates(directory="helpdesk/templates")

PREVIEW_PAGE = """<!doctype html>
<html><head><title>Reply preview</title><link rel="stylesheet" href="/static/ui.css"></head>
<body><main class="preview">{body}</main></body></html>"""


class Draft(BaseModel):
    ticket_text: str


def with_line_breaks(text: str) -> Markup:
    # Summaries come back as short lines; keep the breaks in the template.
    return Markup(text.replace("\n", "<br>"))


def with_line_breaks_escaped(text: str) -> Markup:
    return Markup("<br>").join(text.splitlines())


@router.get("/tickets/{ticket_id}/summary")
def ticket_summary(request: Request, ticket_id: int, text: str):
    message = claude.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=400,
        system=system_prompt("support"),
        messages=[{"role": "user", "content": f"Summarize ticket {ticket_id}:\n{text}"}],
    )
    summary = message.content[0].text
    return templates.TemplateResponse(
        request,
        "ticket_summary.html",
        {
            "ticket_id": ticket_id,
            "summary": with_line_breaks(summary),
            "summary_escaped": with_line_breaks_escaped(summary),
        },
    )


@router.post("/reply-preview", response_class=HTMLResponse)
def reply_preview(draft: Draft):
    completion = openai_client.chat.completions.create(
        model=PLANNER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt("support")},
            {"role": "user", "content": f"Draft a reply in Markdown:\n{draft.ticket_text}"},
        ],
    )
    reply = completion.choices[0].message.content
    return PREVIEW_PAGE.format(body=markdown.markdown(reply, extensions=["tables"]))


@router.post("/reply-preview.txt", response_class=PlainTextResponse)
def reply_preview_text(draft: Draft):
    completion = openai_client.chat.completions.create(
        model=PLANNER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt("support")},
            {"role": "user", "content": f"Draft a reply:\n{draft.ticket_text}"},
        ],
    )
    return completion.choices[0].message.content
