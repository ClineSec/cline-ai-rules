"""After-hours assistant on Amazon Bedrock (Converse API), used when no service-desk agent is on
shift. It can propose paging the on-call engineer or extending a laptop loan.

The staff app streams the reply and keeps the conversation on the device. It runs the tool
requests itself, through the helpdesk API with the signed-in person's own token, so this route
only streams text and tool requests and never acts on them.
"""

import json
import os

import boto3
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/after-hours", tags=["after-hours"])

runtime = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "eu-west-1"))

AFTER_HOURS = {
    "modelId": os.environ.get("AFTER_HOURS_MODEL", "anthropic.claude-sonnet-5-5-v1:0"),
    "system": [
        {
            "text": "You are the Example Corp after-hours IT assistant. Page the on-call engineer "
            "only for outages that affect more than one person."
        }
    ],
    "inferenceConfig": {"maxTokens": 800, "temperature": 0.2},
}

# Kiosk builds can't page anyone; they only get the loan tool.
TOOL_SPECS = {
    "page_on_call": {
        "toolSpec": {
            "name": "page_on_call",
            "description": "Page the on-call infrastructure engineer.",
            "inputSchema": {"json": {"type": "object", "properties": {"summary": {"type": "string"}}}},
        }
    },
    "extend_laptop_loan": {
        "toolSpec": {
            "name": "extend_laptop_loan",
            "description": "Extend a loaner laptop by up to seven days.",
            "inputSchema": {"json": {"type": "object", "properties": {"asset_tag": {"type": "string"}}}},
        }
    },
}
KIOSK_TOOLS = ("extend_laptop_loan",)


def _tool_config(device: str) -> dict:
    names = KIOSK_TOOLS if device == "kiosk" else tuple(TOOL_SPECS)
    return {"tools": [TOOL_SPECS[name] for name in names]}


class AfterHoursChat(BaseModel):
    messages: list[dict]
    device: str = "staff-app"


def _text_events(stream):
    for event in stream["stream"]:
        delta = event.get("contentBlockDelta", {}).get("delta", {})
        if "text" in delta:
            yield delta["text"]
        elif "toolUse" in delta:
            yield "\n" + json.dumps({"tool_input": delta["toolUse"].get("input", "")}) + "\n"


@router.post("/chat")
def after_hours_chat(chat: AfterHoursChat) -> StreamingResponse:
    request = {**AFTER_HOURS, "toolConfig": _tool_config(chat.device), "messages": chat.messages}
    stream = runtime.converse_stream(**request)
    return StreamingResponse(_text_events(stream), media_type="text/plain")


@router.post("/chat/lite")
def after_hours_lite(chat: AfterHoursChat) -> StreamingResponse:
    """Low-bandwidth build: only the person's own words go to the model, as plain text."""
    turns = [
        {"role": "user", "content": [{"text": block["text"]} for block in turn.get("content", []) if "text" in block]}
        for turn in chat.messages
        if turn.get("role") == "user"
    ]
    lite_request = {**AFTER_HOURS, "toolConfig": _tool_config(chat.device), "messages": turns[-10:]}
    stream = runtime.converse_stream(**lite_request)
    return StreamingResponse(_text_events(stream), media_type="text/plain")
