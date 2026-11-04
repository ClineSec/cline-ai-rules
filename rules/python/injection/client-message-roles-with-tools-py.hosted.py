"""A hosted MCP server: OpenAI calls it for the app, with the app's key, so nothing in this file
runs the calls, yet a forged turn steers what the store's admin API is asked to do."""

import os

from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel

app = FastAPI()
client = OpenAI()

STORE_ADMIN = {
    "type": "mcp",
    "server_label": "store_admin",
    "server_url": "https://mcp.example.com/store",
    "headers": {"authorization": f"Bearer {os.environ.get('STORE_ADMIN_TOKEN', '')}"},
    "require_approval": "never",
}


class Chat(BaseModel):
    messages: list[dict]


@app.post("/store/assistant")
def store_assistant(chat: Chat):
    response = client.responses.create(
        model="gpt-5-mini",
        # ruleid: client-message-roles-with-tools-py
        input=chat.messages,
        tools=[STORE_ADMIN],
    )
    return {"text": response.output_text}
