"""Customer reply emails: the assistant drafts a Markdown reply, an agent approves it, and we
send it as plain text plus an HTML part."""

import os
import smtplib
from email.message import EmailMessage

import markdown

from ..llm import PLANNER_MODEL, openai_client, system_prompt

SMTP_HOST = os.environ.get("HELPDESK_SMTP_HOST", "smtp.example.invalid")
FROM_ADDRESS = "IT Helpdesk <helpdesk@example.invalid>"

CLOSED_TEMPLATE = """Your ticket **#{ticket_id}** is closed.

If the problem comes back, reply to this email and we'll reopen it.
"""


def send_approved_reply(to: str, ticket_id: int, ticket_text: str) -> None:
    completion = openai_client.chat.completions.create(
        model=PLANNER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt("support")},
            {"role": "user", "content": f"Draft a reply in Markdown:\n{ticket_text}"},
        ],
    )
    reply = completion.choices[0].message.content
    msg = EmailMessage()
    msg["From"] = FROM_ADDRESS
    msg["To"] = to
    msg["Subject"] = f"Re: ticket #{ticket_id}"
    msg.set_content(reply)
    msg.add_alternative(markdown.markdown(reply, extensions=["tables"]), subtype="html")
    with smtplib.SMTP(SMTP_HOST) as smtp:
        smtp.send_message(msg)


def send_closed_notice(to: str, ticket_id: int) -> None:
    body = CLOSED_TEMPLATE.format(ticket_id=ticket_id)
    msg = EmailMessage()
    msg["From"] = FROM_ADDRESS
    msg["To"] = to
    msg["Subject"] = f"Ticket #{ticket_id} closed"
    msg.set_content(body)
    msg.add_alternative(markdown.markdown(body), subtype="html")
    with smtplib.SMTP(SMTP_HOST) as smtp:
        smtp.send_message(msg)
