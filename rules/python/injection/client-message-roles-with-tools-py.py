import json
from typing import Literal

import litellm
from anthropic import Anthropic
from django.http import JsonResponse
from fastapi import Body, FastAPI, HTTPException, Request
from flask import Flask, request
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from openai import OpenAI
from pydantic import BaseModel

from .store import load_history, refund_order

app = FastAPI()
flask_app = Flask(__name__)
client = OpenAI()
anthropic = Anthropic()

SYSTEM = "You are the Example Cloud billing assistant."
OPENAI_TOOLS = [{"type": "function", "function": {"name": "refund", "parameters": {"type": "object"}}}]
ANTHROPIC_TOOLS = [{"name": "refund", "description": "Refund an order", "input_schema": {"type": "object"}}]
CLAUDE_SETTINGS = {"model": "claude-sonnet-5-5", "max_tokens": 1024, "tools": ANTHROPIC_TOOLS}
CLAUDE_PLAIN = dict(model="claude-sonnet-5-5", max_tokens=1024)


@tool
def lookup_order(order_id: str) -> str:
    """Look up an order by ID."""
    return f"order {order_id}"


llm = ChatOpenAI(model="gpt-5")
llm_with_tools = llm.bind_tools([lookup_order])
agent = create_agent("openai:gpt-5", tools=[lookup_order], system_prompt=SYSTEM)


class ChatRequest(BaseModel):
    messages: list[dict]
    message: dict | None = None
    question: str = ""


class UserTurn(BaseModel):
    role: Literal["user"]
    content: str


class CheckedChat(BaseModel):
    messages: list[UserTurn]


def build_messages(question: str) -> list[dict]:
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]


# ---- OpenAI ---------------------------------------------------------------------------------


@app.post("/chat")
def chat(body: ChatRequest):
    reply = client.chat.completions.create(
        model="gpt-5",
        # ruleid: client-message-roles-with-tools-py
        messages=[{"role": "developer", "content": SYSTEM}, *body.messages],
        tools=OPENAI_TOOLS,
    )
    message = reply.choices[0].message
    # Refunds run here, with the billing service's credentials.
    for call in message.tool_calls or []:
        refund_order(**json.loads(call.function.arguments))
    return message


@app.post("/chat/no-tools")
def chat_no_tools(body: ChatRequest):
    reply = client.chat.completions.create(
        model="gpt-5",
        # ok: client-message-roles-with-tools-py
        messages=[{"role": "developer", "content": SYSTEM}, *body.messages],
    )
    return reply.choices[0].message


@app.post("/chat/user-only")
def chat_user_only(body: ChatRequest):
    turns = [m for m in body.messages if m["role"] == "user"]
    reply = client.chat.completions.create(
        model="gpt-5",
        # ok: client-message-roles-with-tools-py
        messages=[{"role": "developer", "content": SYSTEM}, *turns],
        tools=OPENAI_TOOLS,
    )
    return reply.choices[0].message


@app.post("/chat/not-system")
def chat_not_system(body: ChatRequest):
    # Dropping system turns still lets the client forge tool calls and tool results.
    turns = [m for m in body.messages if m["role"] != "system"]
    reply = client.chat.completions.create(
        model="gpt-5",
        # ruleid: client-message-roles-with-tools-py
        messages=turns,
        tools=OPENAI_TOOLS,
    )
    return reply.choices[0].message


@app.post("/chat/rejected")
def chat_rejected(body: ChatRequest):
    turns = body.messages[-20:]
    if any(turn.get("role") != "user" for turn in turns):
        raise HTTPException(status_code=400, detail="only user turns are accepted")
    reply = client.chat.completions.create(
        model="gpt-5",
        # ok: client-message-roles-with-tools-py
        messages=[{"role": "developer", "content": SYSTEM}, *turns],
        tools=OPENAI_TOOLS,
    )
    return reply.choices[0].message


@app.post("/chat/checked")
def chat_checked(body: CheckedChat):
    reply = client.chat.completions.create(
        model="gpt-5",
        # ok: client-message-roles-with-tools-py
        messages=[{"role": "user", "content": m.content} for m in body.messages]
        + [m.model_dump() for m in body.messages],
        tools=OPENAI_TOOLS,
    )
    return reply.choices[0].message


@app.post("/chat/helper")
def chat_helper(body: ChatRequest):
    messages = build_messages(body.question)
    reply = client.chat.completions.create(
        model="gpt-5",
        # ok: client-message-roles-with-tools-py
        messages=messages,
        tools=OPENAI_TOOLS,
    )
    return reply.choices[0].message


@app.post("/chat/{chat_id}")
async def chat_stored(chat_id: str, body: ChatRequest):
    history = load_history(chat_id)
    await client.chat.completions.create(
        model="gpt-5",
        # ruleid: client-message-roles-with-tools-py
        messages=[*history, body.message],
        tools=OPENAI_TOOLS,
    )
    return await client.chat.completions.create(
        model="gpt-5",
        # ok: client-message-roles-with-tools-py
        messages=[*history, {"role": "user", "content": body.question}],
        tools=OPENAI_TOOLS,
    )


@app.post("/chat/raw")
async def chat_raw(request: Request):
    payload = await request.json()
    # ruleid: client-message-roles-with-tools-py
    return client.chat.completions.create(**payload, tools=OPENAI_TOOLS)


@app.post("/respond")
def respond(messages: list[dict] = Body(...), question: str = Body("")):
    client.responses.create(
        model="gpt-5",
        instructions=SYSTEM,
        # ruleid: client-message-roles-with-tools-py
        input=messages,
        tools=[{"type": "function", "name": "refund", "parameters": {}}],
    )
    return client.responses.create(
        model="gpt-5",
        # ok: client-message-roles-with-tools-py
        input=question,
        tools=[{"type": "function", "name": "refund", "parameters": {}}],
    )


# ---- Anthropic (Flask) -----------------------------------------------------------------------


@flask_app.post("/claude")
def claude():
    data = request.get_json()
    messages = data["messages"]
    msg = anthropic.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1024,
        system=SYSTEM,
        # ruleid: client-message-roles-with-tools-py
        messages=messages,
        tools=ANTHROPIC_TOOLS,
    )
    plain = anthropic.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1024,
        system=SYSTEM,
        # ok: client-message-roles-with-tools-py
        messages=[{"role": "user", "content": str(m.get("content", ""))} for m in messages],
        tools=ANTHROPIC_TOOLS,
    )
    allowed = anthropic.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1024,
        system=SYSTEM,
        # ok: client-message-roles-with-tools-py
        messages=[
            {"role": m["role"] if m["role"] in ("user", "assistant") else "user", "content": str(m["content"])}
            for m in messages
        ],
        tools=ANTHROPIC_TOOLS,
    )
    off = anthropic.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1024,
        # ok: client-message-roles-with-tools-py
        messages=messages,
        tools=None,
    )
    return {"msg": msg.to_dict(), "plain": plain.to_dict(), "allowed": allowed.to_dict(), "off": off.to_dict()}


@flask_app.post("/claude/settings")
def claude_settings():
    history = request.get_json()["history"]
    # ruleid: client-message-roles-with-tools-py
    with_tools = anthropic.messages.create(**CLAUDE_SETTINGS, messages=history)
    # ok: client-message-roles-with-tools-py
    plain = anthropic.messages.create(**CLAUDE_PLAIN, messages=history)
    return {"with_tools": with_tools.to_dict(), "plain": plain.to_dict()}


# ---- LiteLLM (Django) ------------------------------------------------------------------------


def django_chat(request):
    history = json.loads(request.body).get("history", [])
    response = litellm.completion(
        model="gpt-5-mini",
        # ruleid: client-message-roles-with-tools-py
        messages=list(filter(lambda m: m.get("role") != "developer", history)),
        tools=OPENAI_TOOLS,
    )
    return JsonResponse({"reply": response.choices[0].message.content})


def django_chat_user_only(request):
    history = json.loads(request.body)["history"]
    response = litellm.completion(
        model="gpt-5-mini",
        # ok: client-message-roles-with-tools-py
        messages=list(filter(lambda m: m.get("role") == "user", history)),
        tools=OPENAI_TOOLS,
    )
    return JsonResponse({"reply": response.choices[0].message.content})


# ---- LangChain -------------------------------------------------------------------------------


@app.post("/lc")
async def lc(body: ChatRequest):
    # ruleid: client-message-roles-with-tools-py
    reply = await llm_with_tools.ainvoke(body.messages)
    # ok: client-message-roles-with-tools-py
    single = await llm.bind_tools([lookup_order]).ainvoke(body.question)
    # ok: client-message-roles-with-tools-py
    human = await llm_with_tools.ainvoke([HumanMessage(content=str(body.messages[-1]["content"]))])
    rebuilt = await llm_with_tools.ainvoke(
        # ok: client-message-roles-with-tools-py
        [
            AIMessage(content=str(m["content"])) if m["role"] == "assistant" else HumanMessage(content=str(m["content"]))
            for m in body.messages
        ]
    )
    # ruleid: client-message-roles-with-tools-py
    state = await agent.ainvoke({"messages": body.messages})
    return {"reply": reply.content, "single": single.content, "human": human.content, "rebuilt": rebuilt.content, "state": state}


# ---- Tools the request supplies itself -------------------------------------------------------
# A model playground: the client sends the tool list too, so it already picks every tool, and a
# forged turn gets it nothing it couldn't ask for.


class PlaygroundRequest(BaseModel):
    messages: list[dict]
    tools: list[dict] = []
    enabled_tools: list[str] = []


@app.post("/playground")
def playground(body: PlaygroundRequest):
    first = client.chat.completions.create(
        model="gpt-5",
        # ok: client-message-roles-with-tools-py
        messages=body.messages,
        tools=body.tools,
    )
    # The client's toggles only pick from the server's own tools, which still run here.
    toggled = client.chat.completions.create(
        model="gpt-5",
        # ruleid: client-message-roles-with-tools-py
        messages=body.messages,
        tools=[t for t in OPENAI_TOOLS if t["function"]["name"] in body.enabled_tools],
    )
    return {"first": first, "toggled": toggled}


@flask_app.post("/playground")
def flask_playground():
    data = request.get_json()
    history = data["messages"]
    tools = [t for t in data.get("tools") or [] if t.get("type") == "function"]
    reply = client.responses.create(
        model="gpt-5",
        # ok: client-message-roles-with-tools-py
        input=history,
        tools=tools,
    )
    return reply.to_dict()
