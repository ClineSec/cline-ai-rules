"""The model call returns tool calls and the route hands them to a runner in another module,
which applies them with the billing service's credentials."""

from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel

from .billing_tools import BILLING_TOOLS, run_tool_calls

app = FastAPI()
client = OpenAI()


class Chat(BaseModel):
    messages: list[dict]


@app.post("/billing/assistant")
def billing_assistant(chat: Chat):
    completion = client.chat.completions.create(
        model="gpt-5-mini",
        # ruleid: client-message-roles-with-tools-py
        messages=chat.messages,
        tools=BILLING_TOOLS,
    )
    message = completion.choices[0].message
    if len(message.tool_calls or []):
        run_tool_calls(message.tool_calls)
    return message.model_dump()
