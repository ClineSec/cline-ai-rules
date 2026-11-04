"""Thumbs-up / thumbs-down feedback on the assistant's answers in the agent console.

Helpful answers become fine-tuning examples for the next helpdesk-assist model (the nightly
job in ops/ uploads `helpful_answers.jsonl`); unhelpful ones go to the QA review queue.
"""

import json
import os
import time
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from .llm import system_prompt
from .reporting import feedback_queue

router = APIRouter(prefix="/feedback")

DATA_ROOT = Path(os.environ.get("HELPDESK_DATA", "/srv/helpdesk/data"))
FINETUNE_DIR = DATA_ROOT / "finetune"
HELPFUL_ANSWERS = FINETUNE_DIR / "helpful_answers.jsonl"
FEEDBACK_AUDIT_LOG = DATA_ROOT / "audit" / "answer_feedback.jsonl"


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AnswerFeedback(BaseModel):
    ticket_id: str
    team: Literal["IT", "Facilities", "Security"] = "IT"
    vote: Literal["up", "down"]
    turns: list[Turn]
    comment: str = ""


def _as_example(team: str, turns: list[Turn]) -> dict:
    """One chat-format fine-tuning example: the team's system prompt, then the conversation."""
    messages = [{"role": "system", "content": system_prompt(team)}]
    messages += [{"role": t.role, "content": t.content} for t in turns]
    return {"messages": messages}


class JsonlLog:
    """Append-only JSON Lines file; one record per line."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, record: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as out:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")


feedback_audit = JsonlLog(FEEDBACK_AUDIT_LOG)
helpful_answers = JsonlLog(HELPFUL_ANSWERS)


@router.post("/answers")
def answer_feedback(fb: AnswerFeedback) -> dict:
    feedback_audit.append({"ticket": fb.ticket_id, "vote": fb.vote, "at": time.time()})
    if fb.vote == "up":
        helpful_answers.append(_as_example(fb.team, fb.turns))
    else:
        feedback_queue.put({"ticket": fb.ticket_id, "turns": [t.model_dump() for t in fb.turns], "comment": fb.comment})
    return {"ok": True}
