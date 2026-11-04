"""Self-service portal assistant: password, MFA, and account-lock help for signed-in staff.

The portal's chat panel keeps the conversation in the browser and posts it with every turn.
The tools below run with the helpdesk's directory service account.
"""

import json
import os

import httpx
from fastapi import APIRouter, Header
from pydantic import BaseModel

from .llm import PLANNER_MODEL, openai_client

router = APIRouter(prefix="/portal/assistant", tags=["portal"])

PORTAL_SYSTEM = (
    "You are the Example Corp IT self-service assistant. You may unlock the caller's own "
    "account and re-enrol their MFA device. Anything about another person's account goes "
    "to the service desk."
)

PORTAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "unlock_account",
            "description": "Unlock a directory account after too many failed sign-ins.",
            "parameters": {
                "type": "object",
                "properties": {"username": {"type": "string"}},
                "required": ["username"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_mfa",
            "description": "Remove a user's MFA devices so they can enrol a new one.",
            "parameters": {
                "type": "object",
                "properties": {"username": {"type": "string"}},
                "required": ["username"],
            },
        },
    },
]


DIRECTORY_API = "https://directory.example.com/api/v1"


def _directory(action: str, username: str) -> str:
    resp = httpx.post(
        f"{DIRECTORY_API}/accounts/{username}/{action}",
        headers={"authorization": f"Bearer {os.environ.get('DIRECTORY_SERVICE_TOKEN', '')}"},
        timeout=10,
    )
    return resp.text


PORTAL_ACTIONS = {
    "unlock_account": lambda username: _directory("unlock", username),
    "reset_mfa": lambda username: _directory("mfa-reset", username),
}


class PortalChat(BaseModel):
    messages: list[dict]
    page: str = "home"


def _complete(conversation: list[dict]):
    return openai_client.chat.completions.create(
        model=PLANNER_MODEL,
        messages=[{"role": "system", "content": PORTAL_SYSTEM}, *conversation],
        tools=PORTAL_TOOLS,
        tool_choice="auto",
    )


@router.post("")
def ask(chat: PortalChat, x_portal_user: str = Header()) -> dict:
    completion = _complete(chat.messages)
    message = completion.choices[0].message
    # Unlocks and MFA resets run here, as the directory service account.
    done = [
        PORTAL_ACTIONS[call.function.name](**json.loads(call.function.arguments))
        for call in message.tool_calls or []
    ]
    return {"reply": message.content, "done": done}


@router.post("/quick")
def quick_answer(chat: PortalChat, x_portal_user: str = Header()) -> dict:
    """The kiosk build only shows the latest answer, so only the caller's own words are sent."""
    asked = [
        {"role": "user", "content": str(turn.get("content", ""))}
        for turn in chat.messages
        if turn.get("role") == "user"
    ]
    completion = _complete(asked[-6:])
    return {"reply": completion.choices[0].message.content}
