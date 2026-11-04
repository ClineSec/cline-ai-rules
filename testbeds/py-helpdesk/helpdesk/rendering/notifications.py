"""Ticket update emails with the assistant's suggested reply."""

from jinja2 import Environment, PackageLoader, select_autoescape

from ..llm import TRIAGE_MODEL, claude, system_prompt

# trim_blocks keeps the plain-text templates tidy.
email_env = Environment(loader=PackageLoader("helpdesk", "templates/email"), trim_blocks=True)
digest_env = Environment(
    loader=PackageLoader("helpdesk", "templates/email"), autoescape=select_autoescape()
)


def suggested_reply(ticket_text: str) -> str:
    message = claude.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=600,
        system=system_prompt("support"),
        messages=[{"role": "user", "content": f"Suggest a reply:\n{ticket_text}"}],
    )
    return message.content[0].text


def ticket_update_email(ticket_id: int, requester: str, ticket_text: str) -> tuple[str, str]:
    message = claude.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=600,
        system=system_prompt("support"),
        messages=[{"role": "user", "content": f"Suggest a reply:\n{ticket_text}"}],
    )
    reply = message.content[0].text
    context = {"ticket_id": ticket_id, "requester": requester}
    html_body = email_env.get_template("ticket_update.html").render(context, reply=reply)
    text_body = email_env.get_template("ticket_update.txt").render(context, reply=reply)
    return html_body, text_body


def weekly_digest(tickets: list[dict]) -> str:
    replies = [suggested_reply(t["text"]) for t in tickets]
    return digest_env.get_template("digest.html").render(tickets=tickets, replies=replies)
