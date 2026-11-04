"""Ask-the-data reports for team leads.

Leads type a question ("how many printer tickets are still open on floor 2?") and get rows back
from the ticket warehouse, a read-only SQLite copy of the helpdesk database refreshed nightly.
The model writes the query; the warehouse connection is opened read-only.
"""

import json
import re
import sqlite3
from pathlib import Path

import litellm
import pandas as pd
import sqlalchemy as sa

from .llm import PLANNER_MODEL, TRIAGE_MODEL, claude, openai_client

WAREHOUSE = Path("/srv/helpdesk/warehouse.sqlite")
REPORT_ENGINE = sa.create_engine(f"sqlite:///file:{WAREHOUSE}?mode=ro&uri=true")

SCHEMA_HINT = """\
tickets(id TEXT, queue TEXT, status TEXT, opened_at TEXT, closed_at TEXT, assignee TEXT)
queues(name TEXT, team TEXT)
"""
SQL_INSTRUCTIONS = (
    "Write one SQLite SELECT statement that answers the question, using only these tables:\n"
    + SCHEMA_HINT
    + "Reply with the SQL only."
)

SORT_ORDERS = {
    "newest": "opened_at DESC",
    "oldest": "opened_at ASC",
    "assignee": "assignee, opened_at DESC",
}
SAVED_VIEWS = {"open_by_queue", "closed_last_week", "aging_tickets"}

tickets = sa.table("tickets", sa.column("id"), sa.column("queue"), sa.column("status"))

_FENCE = re.compile(r"^```(?:sql)?\s*|\s*```$", re.MULTILINE)


def _readonly() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{WAREHOUSE}?mode=ro", uri=True)


def _fetch(query: str, params: tuple = (), limit: int | None = None) -> list[tuple]:
    """Run one query on the read-only warehouse; every report path goes through here."""
    with _readonly() as warehouse:
        cursor = warehouse.execute(query, params)
        return cursor.fetchmany(limit) if limit else cursor.fetchall()


def strip_fences(text: str) -> str:
    """Models like to wrap SQL in a Markdown code fence."""
    return _FENCE.sub("", text).strip()


def write_query(question: str) -> str:
    resp = openai_client.chat.completions.create(
        model=PLANNER_MODEL,
        messages=[
            {"role": "system", "content": SQL_INSTRUCTIONS},
            {"role": "user", "content": question},
        ],
    )
    return strip_fences(resp.choices[0].message.content)


def answer(question: str) -> list[tuple]:
    return _fetch(write_query(question), limit=200)


def export_csv(question: str, dest: Path) -> int:
    msg = claude.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=1024,
        system=SQL_INSTRUCTIONS,
        messages=[{"role": "user", "content": question}],
    )
    query = strip_fences(msg.content[0].text)
    frame = pd.read_sql_query(sa.text(query), REPORT_ENGINE)
    frame.to_csv(dest, index=False)
    return len(frame)


def ticket_list(request_text: str) -> list[tuple]:
    out = litellm.completion(
        model=PLANNER_MODEL,
        messages=[
            {
                "role": "system",
                "content": 'Return JSON: {"queue": <queue name>, "order_by": <SQL ORDER BY clause>}',
            },
            {"role": "user", "content": request_text},
        ],
        response_format={"type": "json_object"},
    )
    plan = json.loads(out.choices[0].message.content)
    order = plan.get("order_by", "opened_at DESC")
    return _fetch(
        f"SELECT id, queue, status FROM tickets WHERE queue = ? ORDER BY {order} LIMIT 50",
        (plan["queue"],),
    )


def ticket_list_sorted(request_text: str) -> list[tuple]:
    """The version the dashboard uses: the model picks a named sort, not SQL."""
    out = litellm.completion(
        model=PLANNER_MODEL,
        messages=[
            {"role": "system", "content": 'Return JSON: {"queue": <queue name>, "sort": "newest" | "oldest" | "assignee"}'},
            {"role": "user", "content": request_text},
        ],
        response_format={"type": "json_object"},
    )
    plan = json.loads(out.choices[0].message.content)
    order = SORT_ORDERS.get(plan.get("sort"), SORT_ORDERS["newest"])
    return _fetch(
        f"SELECT id, queue, status, assignee FROM tickets WHERE queue = ? ORDER BY {order} LIMIT 50",
        (plan["queue"],),
    )


def saved_view(request_text: str) -> pd.DataFrame:
    resp = openai_client.responses.create(
        model=PLANNER_MODEL,
        instructions="Name the saved report that best answers the request: "
        + ", ".join(sorted(SAVED_VIEWS)),
        input=request_text,
    )
    view = resp.output_text.strip()
    if view not in SAVED_VIEWS:
        raise ValueError(f"unknown report {view!r}")
    return pd.read_sql_query(f"SELECT * FROM {view}", REPORT_ENGINE)


def open_count(request_text: str) -> int:
    resp = openai_client.responses.create(
        model=PLANNER_MODEL,
        instructions="Reply with the queue name the request is about, nothing else.",
        input=request_text,
    )
    queue = resp.output_text.strip()
    stmt = (
        sa.select(sa.func.count())
        .select_from(tickets)
        .where(tickets.c.queue == queue, tickets.c.status == "open")
    )
    with REPORT_ENGINE.connect() as conn:
        return conn.execute(stmt).scalar_one()
