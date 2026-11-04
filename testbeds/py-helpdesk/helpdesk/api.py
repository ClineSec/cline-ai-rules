"""HTTP API for the helpdesk assistant."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from . import diagnostics, estimates, remediation
from .assist import router as assist_router
from .assist_chat import router as portal_router
from .rendering.pages import router as ui_router
from .llm import TRIAGE_MODEL, claude, system_prompt

app = FastAPI(title="helpdesk")
app.include_router(assist_router)
app.include_router(portal_router)
app.include_router(ui_router)
runner = diagnostics.DiagnosticsRunner()


class Ticket(BaseModel):
    text: str
    open_tickets: int = 0


@app.post("/tickets/fix")
def fix(ticket: Ticket) -> dict:
    return {"output": runner.run_suggested_fix(ticket.text)}


@app.post("/tickets/check")
def check(ticket: Ticket) -> dict:
    return {"output": runner.run_approved_check(ticket.text)}


@app.post("/tickets/estimate")
def estimate(ticket: Ticket) -> dict:
    return {"hours": estimates.estimate_hours(ticket.text, ticket.open_tickets)}


@app.post("/tickets/remediate")
async def remediate(ticket: Ticket) -> dict:
    await remediation.log_summary(ticket.text)
    return {"output": await remediation.remediate(ticket.text)}


@app.post("/tickets/answer")
def answer(ticket: Ticket, team: str = "IT") -> dict:
    reply = claude.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=600,
        system=system_prompt(team),
        messages=[{"role": "user", "content": ticket.text}],
    )
    return {"answer": reply.content[0].text}


@app.post("/tickets/answer/urgent")
def answer_urgent(ticket: Ticket, priority: Literal["high", "critical"] = "high") -> dict:
    reply = claude.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=600,
        system=system_prompt("IT") + f" This ticket is {priority} priority; give the fastest workaround first.",
        messages=[{"role": "user", "content": ticket.text}],
    )
    return {"answer": reply.content[0].text}
