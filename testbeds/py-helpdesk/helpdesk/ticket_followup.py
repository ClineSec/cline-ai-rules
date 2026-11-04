"""Follow-up questions on an open ticket, answered by the triage model with ticket tools.

The ticket thread is stored by the helpdesk; the requester's app sends only its newest message.
"""

import sqlite3
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from .llm import TRIAGE_MODEL, claude

router = APIRouter(prefix="/tickets", tags=["tickets"])

THREADS_DB = Path(__file__).resolve().parent.parent / "var" / "threads.sqlite3"

TICKET_TOOLS = [
    {
        "name": "set_priority",
        "description": "Change the ticket's priority (P1 pages the on-call engineer).",
        "input_schema": {
            "type": "object",
            "properties": {"priority": {"type": "string", "enum": ["P1", "P2", "P3", "P4"]}},
            "required": ["priority"],
        },
    },
    {
        "name": "add_watcher",
        "description": "Add someone to the ticket's watchers.",
        "input_schema": {
            "type": "object",
            "properties": {"email": {"type": "string"}},
            "required": ["email"],
        },
    },
]

FOLLOWUP_SETTINGS = {
    "model": TRIAGE_MODEL,
    "max_tokens": 1024,
    "system": "You answer follow-up questions about an IT ticket and keep its fields up to date.",
    "tools": TICKET_TOOLS,
}


def apply_ticket_action(ticket_id: str, name: str, args: dict) -> str:
    """Apply a tool call to the ticket, as the helpdesk."""
    with sqlite3.connect(THREADS_DB) as db:
        if name == "set_priority":
            db.execute("UPDATE tickets SET priority = ? WHERE id = ?", (args["priority"], ticket_id))
        elif name == "add_watcher":
            db.execute("INSERT INTO watchers (ticket_id, email) VALUES (?, ?)", (ticket_id, args["email"]))
    return "done"


def load_thread(ticket_id: str) -> list[dict]:
    with sqlite3.connect(THREADS_DB) as db:
        rows = db.execute(
            "SELECT role, content FROM thread_messages WHERE ticket_id = ? ORDER BY position",
            (ticket_id,),
        ).fetchall()
    return [{"role": role, "content": content} for role, content in rows]


class FollowUp(BaseModel):
    message: dict


class FollowUpText(BaseModel):
    text: str


@router.post("/{ticket_id}/followup")
def follow_up(ticket_id: str, body: FollowUp) -> dict:
    thread = load_thread(ticket_id)
    reply = claude.messages.create(**FOLLOWUP_SETTINGS, messages=[*thread, body.message])
    # Priority changes and new watchers are applied here; the results are stored with the thread.
    results = [
        {"type": "tool_result", "tool_use_id": block.id, "content": apply_ticket_action(ticket_id, block.name, block.input)}
        for block in reply.content
        if block.type == "tool_use"
    ]
    return {"reply": reply.to_dict(), "tool_results": results}


@router.post("/{ticket_id}/followup/text")
def follow_up_text(ticket_id: str, body: FollowUpText) -> dict:
    thread = load_thread(ticket_id)
    reply = claude.messages.create(
        **FOLLOWUP_SETTINGS,
        messages=[*thread, {"role": "user", "content": body.text}],
    )
    return reply.to_dict()
