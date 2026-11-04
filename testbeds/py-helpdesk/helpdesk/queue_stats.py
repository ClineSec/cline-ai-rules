"""Queue health numbers for the morning stand-up bot."""

import sqlalchemy as sa

from .llm import PLANNER_MODEL, openai_client

ENGINE = sa.create_engine("sqlite:///file:/srv/helpdesk/warehouse.sqlite?mode=ro&uri=true")
tickets = sa.table("tickets", sa.column("id"), sa.column("queue"), sa.column("status"), sa.column("opened_at"))


def _queue_for(message: str) -> str:
    resp = openai_client.responses.create(
        model=PLANNER_MODEL,
        instructions="Reply with the helpdesk queue name the message is about, nothing else.",
        input=message,
    )
    return resp.output_text.strip()


def open_tickets(message: str) -> int:
    queue = _queue_for(message)
    stmt = sa.select(sa.func.count()).select_from(tickets).where(tickets.c.queue == queue, tickets.c.status == "open")
    with ENGINE.connect() as conn:
        return conn.execute(stmt).scalar_one()


def oldest_open(message: str) -> list:
    resp = openai_client.responses.create(
        model=PLANNER_MODEL,
        instructions="Reply with the helpdesk queue name the message is about, nothing else.",
        input=message,
    )
    stmt = sa.text("SELECT id, opened_at FROM tickets WHERE queue = :queue AND status = 'open' ORDER BY opened_at LIMIT 5")
    with ENGINE.connect() as conn:
        return conn.execute(stmt, {"queue": resp.output_text.strip()}).all()
