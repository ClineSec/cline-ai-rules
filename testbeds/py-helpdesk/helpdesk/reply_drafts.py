"""Reply drafting for helpdesk agents: alternative replies, thread digests, and fix-it plans.

Agents pick how long a draft may run and how many versions to compare from the console.
"""

import asyncio
from typing import Literal

from agents import Agent, Runner
from fastapi import APIRouter, Header
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .llm import PLANNER_MODEL, TRIAGE_MODEL, claude_async, openai_client
from .ticket_followup import load_thread

router = APIRouter(prefix="/drafts", tags=["drafts"])

# Draft budgets by plan. The plan comes from the account record, not from the request.
PLAN_DRAFT_TOKENS = {"starter": 400, "team": 900, "enterprise": 1600}
ACCOUNT_PLANS = {"acct-demo": "starter"}
MAX_QUICK_REPLIES = 3

TONE_HINTS = {
    "formal": "Write a formal reply.",
    "friendly": "Write a short, friendly reply.",
}

fixit_planner = Agent(
    name="fix-it planner",
    instructions="Turn the ticket into a numbered list of safe troubleshooting steps.",
    model=PLANNER_MODEL,
)


class DraftRequest(BaseModel):
    ticket_text: str
    tone: Literal["formal", "friendly"] = "friendly"
    # Longer tickets need room for a longer reply.
    length: int = 500
    alternatives: int = 2


class OutlineRequest(BaseModel):
    ticket_text: str
    sections: int = Field(3, ge=1, le=6)
    length: int = Field(400, ge=50, le=1200)


class PlanRequest(BaseModel):
    ticket_text: str
    steps: int = 8


def _user_turn(text: str, tone: str) -> list[dict]:
    return [{"role": "user", "content": f"{TONE_HINTS[tone]}\n\nTicket:\n{text}"}]


def _thread_text(ticket_id: str) -> str:
    return "\n".join(m["content"] for m in load_thread(ticket_id))


async def _draft_once(text: str, tone: str, max_tokens: int = 300, temperature: float = 0.7):
    return await claude_async.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=_user_turn(text, tone),
    )


@router.post("/alternatives")
async def alternatives(req: DraftRequest) -> dict:
    tasks = []
    async with asyncio.TaskGroup() as tg:
        for _ in range(req.alternatives):
            draft = _draft_once(req.ticket_text, req.tone, max_tokens=req.length, temperature=0.8)
            tasks.append(tg.create_task(draft))
    return {"drafts": [t.result().content[0].text for t in tasks]}


@router.post("/quick-replies")
async def quick_replies(req: DraftRequest) -> dict:
    # Same console form, but the server decides how many versions and how long.
    count = min(req.alternatives, MAX_QUICK_REPLIES)
    replies = await asyncio.gather(*(_draft_once(req.ticket_text, req.tone) for _ in range(count)))
    return {"replies": [r.content[0].text for r in replies]}


@router.post("/short-replies")
async def short_replies(req: DraftRequest) -> dict:
    # Keep drafting until enough replies fit in a chat bubble.
    kept: list[str] = []
    while req.alternatives > len(kept):
        reply = await claude_async.messages.create(
            model=TRIAGE_MODEL,
            max_tokens=300,
            messages=_user_turn(req.ticket_text, req.tone),
        )
        text = reply.content[0].text
        if len(text) < 600:
            kept.append(text)
    return {"replies": kept}


@router.get("/digest/{ticket_id}")
def digest(ticket_id: str, words: int = 250) -> dict:
    # About two tokens a word, so the summary has room to finish.
    summarizer = ChatOpenAI(model=PLANNER_MODEL, max_tokens=words * 2, temperature=0)
    summary = summarizer.invoke(f"Summarize this ticket thread:\n\n{_thread_text(ticket_id)}")
    return {"digest": summary.content}


@router.post("/outline")
def outline(req: OutlineRequest) -> dict:
    parts = []
    for n in range(req.sections):
        part = openai_client.responses.create(
            model=PLANNER_MODEL,
            input=f"Write part {n + 1} of a reply outline for:\n{req.ticket_text}",
            max_output_tokens=req.length,
        )
        parts.append(part.output_text)
    return {"outline": parts}


@router.post("/plan-draft")
async def plan_draft(req: DraftRequest, x_account_id: str = Header(...)) -> dict:
    plan = ACCOUNT_PLANS.get(x_account_id, "starter")
    reply = await claude_async.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=PLAN_DRAFT_TOKENS[plan],
        messages=_user_turn(req.ticket_text, req.tone),
    )
    return {"draft": reply.content[0].text}


@router.post("/fix-it")
async def fix_it(req: PlanRequest) -> dict:
    result = await Runner.run(fixit_planner, req.ticket_text, max_turns=req.steps)
    return {"plan": result.final_output}
