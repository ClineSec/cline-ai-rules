"""Routes that only hand the model's tool calls back to the browser, which runs them by calling
the app's own APIs as the signed-in user. Nothing in this file runs a tool call, so a forged
system, assistant, or tool turn gets the sender nothing they couldn't get by asking."""

import boto3
import litellm
from anthropic import Anthropic
from fastapi import FastAPI
from flask import Flask, request
from langchain_openai import ChatOpenAI
from openai import OpenAI
from pydantic import BaseModel

from .catalog import CATALOG_TOOLS, CLAUDE_TOOLS, CONVERSE_TOOLS, lookup_product

app = FastAPI()
flask_app = Flask(__name__)
client = OpenAI()
anthropic = Anthropic()
runtime = boto3.client("bedrock-runtime")
shopper = ChatOpenAI(model="gpt-5-mini").bind_tools([lookup_product])


class Chat(BaseModel):
    messages: list[dict]


@app.post("/assistant/turn")
def turn(chat: Chat):
    response = client.chat.completions.parse(
        model="gpt-5-mini",
        # ok: client-message-roles-with-tools-py
        messages=chat.messages,
        tools=CATALOG_TOOLS,
        parallel_tool_calls=False,
    )
    message = response.choices[0].message
    print(message.tool_calls)
    return message.model_dump()


@app.post("/assistant/claude")
def claude_turn(chat: Chat):
    reply = anthropic.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1024,
        # ok: client-message-roles-with-tools-py
        messages=chat.messages,
        tools=CLAUDE_TOOLS,
    )
    converse = runtime.converse(
        modelId="anthropic.claude-sonnet-5-5-v1:0",
        # ok: client-message-roles-with-tools-py
        messages=chat.messages,
        toolConfig=CONVERSE_TOOLS,
    )
    routed = litellm.completion(
        model="gpt-5-mini",
        # ok: client-message-roles-with-tools-py
        messages=chat.messages,
        tools=CATALOG_TOOLS,
    )
    # ok: client-message-roles-with-tools-py
    proposal = shopper.invoke(chat.messages)
    return {
        "reply": reply.to_dict(),
        "converse": converse["output"],
        "routed": routed.choices[0].message.tool_calls,
        "proposal": proposal.tool_calls,
    }


@flask_app.post("/assistant/stream")
def stream_turn():
    events = client.responses.create(
        model="gpt-5-mini",
        # ok: client-message-roles-with-tools-py
        input=request.get_json()["messages"],
        tools=[{"type": "function", "name": t["function"]["name"], "parameters": {}} for t in CATALOG_TOOLS],
        stream=True,
    )
    return flask_app.response_class((e.to_json() for e in events), mimetype="text/event-stream")
