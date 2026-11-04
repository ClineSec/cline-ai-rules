"""Agent assist: drafts and summaries that a support agent reviews before sending."""

from typing import Annotated, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from .llm import PLANNER_MODEL, TRIAGE_MODEL, claude, openai_client

router = APIRouter(prefix="/assist", tags=["assist"])

SUPPORTED_LANGUAGES = {"en", "de", "fr", "es", "nl"}

# Reply styles the support leads maintain; the agent's client sends the key.
REPLY_STYLES = {
    "concise": "Keep the reply under 120 words and lead with the fix.",
    "walkthrough": "Walk the requester through the fix one step per line.",
    "apology": "Acknowledge the delay in one sentence, then give the fix.",
}


class DraftRequest(BaseModel):
    ticket_text: str
    tone: Literal["friendly", "neutral", "formal"] = "friendly"
    style: str = "concise"
    language: str = "en"
    signature: str = ""


class SummaryRequest(BaseModel):
    ticket_text: str
    audience: str = "the requester"


class Macro(BaseModel):
    id: int
    title: str
    instructions: str


def get_macro(macro_id: int) -> Macro:
    """Saved reply macros, edited by support leads in the admin console."""
    raise NotImplementedError("backed by the admin console's macro table")


def _draft(system: str, ticket_text: str) -> str:
    reply = claude.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": ticket_text}],
    )
    return reply.content[0].text


@router.post("/draft")
def draft_reply(
    body: DraftRequest,
    x_agent_team: Annotated[str, Header()] = "service desk",
) -> dict:
    if body.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=422, detail="unsupported language")
    system = (
        f"You draft replies for the {x_agent_team} team at Example Cloud. "
        f"Write in {body.language} with a {body.tone} tone. "
        + REPLY_STYLES.get(body.style, REPLY_STYLES["concise"])
    )
    if body.signature:
        system += f"\n\nEnd the reply with the agent's signature:\n{body.signature}"
    return {"draft": _draft(system, body.ticket_text)}


@router.post("/draft/macro/{macro_id}")
def draft_from_macro(macro_id: int, body: DraftRequest) -> dict:
    macro = get_macro(macro_id)
    if body.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=422, detail="unsupported language")
    system = f"{macro.instructions}\n\nWrite in {body.language} with a {body.tone} tone."
    return {"draft": _draft(system, body.ticket_text), "macro": macro.title}


@router.post("/summary")
def summarize_for(body: SummaryRequest) -> dict:
    """A summary of the ticket for whoever the agent is forwarding it to."""
    reply = openai_client.responses.create(
        model=PLANNER_MODEL,
        instructions=f"Summarize this helpdesk ticket for {body.audience}. Use plain language.",
        input=body.ticket_text,
    )
    return {"summary": reply.output_text}
