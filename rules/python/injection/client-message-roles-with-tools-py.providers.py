import boto3
from agents import Agent, Runner, function_tool
from fastapi import FastAPI, Request
from google import genai
from google.genai import types
from pydantic import BaseModel
from pydantic_ai import Agent as PydanticAgent
from pydantic_ai import ModelMessagesTypeAdapter

app = FastAPI()
gemini = genai.Client()
runtime = boto3.client("bedrock-runtime")

REFUND = types.FunctionDeclaration(name="refund", description="Refund an order")
GEMINI_CONFIG = types.GenerateContentConfig(
    system_instruction="You handle refunds.", tools=[types.Tool(function_declarations=[REFUND])]
)
PLAIN_CONFIG = {"temperature": 0}
TOOL_CONFIG = {"tools": [{"toolSpec": {"name": "refund", "inputSchema": {"json": {"type": "object"}}}}]}


def refund(order_id: str) -> str:
    """Refund an order."""
    return f"refunded {order_id}"


@function_tool
def refund_order(order_id: str) -> str:
    """Refund an order."""
    return f"refunded {order_id}"


billing_agent = Agent(name="Billing", instructions="You handle refunds.", tools=[refund_order])
greeter = Agent(name="Greeter", instructions="Say hello.")

support = PydanticAgent("openai:gpt-5", instructions="You handle refunds.")
plain_agent = PydanticAgent("openai:gpt-5", instructions="Say hello.")


@support.tool_plain
def lookup_order(order_id: str) -> str:
    """Look up an order."""
    return f"order {order_id}"


class Chat(BaseModel):
    history: list[dict]
    message: str = ""


# ---- Gemini ----------------------------------------------------------------------------------


@app.post("/gemini")
def gemini_chat(body: Chat):
    a = gemini.models.generate_content(
        model="gemini-flash-latest",
        # ruleid: client-message-roles-with-tools-py
        contents=body.history,
        config=GEMINI_CONFIG,
    )
    b = gemini.models.generate_content_stream(
        model="gemini-flash-latest",
        # ruleid: client-message-roles-with-tools-py
        contents=body.history,
        config=types.GenerateContentConfig(tools=[refund]),
    )
    c = gemini.chats.create(
        model="gemini-flash-latest",
        # ruleid: client-message-roles-with-tools-py
        history=body.history,
        config={"tools": [refund]},
    )
    return {"a": a.text, "b": bool(b), "c": bool(c)}


@app.post("/gemini/plain")
async def gemini_plain(body: Chat):
    a = await gemini.aio.models.generate_content(
        model="gemini-flash-latest",
        # ok: client-message-roles-with-tools-py
        contents=body.history,
        config=PLAIN_CONFIG,
    )
    b = await gemini.aio.models.generate_content(
        model="gemini-flash-latest",
        # ok: client-message-roles-with-tools-py
        contents=[c for c in body.history if c.get("role") == "user"],
        config=GEMINI_CONFIG,
    )
    c = await gemini.aio.models.generate_content(
        model="gemini-flash-latest",
        # ok: client-message-roles-with-tools-py
        contents=body.message,
        config=GEMINI_CONFIG,
    )
    return {"a": a.text, "b": b.text, "c": c.text}


# ---- Bedrock Converse ------------------------------------------------------------------------


@app.post("/bedrock")
async def bedrock_chat(request: Request):
    payload = await request.json()
    out = runtime.converse(
        modelId="anthropic.claude-sonnet-5-5-v1:0",
        system=[{"text": "You handle refunds."}],
        # ruleid: client-message-roles-with-tools-py
        messages=payload["messages"],
        toolConfig=TOOL_CONFIG,
    )
    plain = runtime.converse(
        modelId="anthropic.claude-sonnet-5-5-v1:0",
        # ok: client-message-roles-with-tools-py
        messages=payload["messages"],
    )
    user_only = runtime.converse_stream(
        modelId="anthropic.claude-sonnet-5-5-v1:0",
        # ok: client-message-roles-with-tools-py
        messages=[{"role": "user", "content": m["content"]} for m in payload["messages"]],
        toolConfig=TOOL_CONFIG,
    )
    # Refunds run here; their results go back to the model on the next turn.
    tool_results = [
        {"toolResult": {"toolUseId": block["toolUse"]["toolUseId"], "content": [{"text": "queued"}]}}
        for block in out["output"]["message"]["content"]
        if "toolUse" in block
    ]
    return {"out": out, "tool_results": tool_results, "plain": plain, "user_only": bool(user_only)}


# ---- OpenAI Agents SDK -----------------------------------------------------------------------


@app.post("/agents")
async def agents_chat(body: Chat):
    # ruleid: client-message-roles-with-tools-py
    result = await Runner.run(billing_agent, body.history)
    # ruleid: client-message-roles-with-tools-py
    streamed = Runner.run_streamed(billing_agent, input=body.history, max_turns=4)
    # ok: client-message-roles-with-tools-py
    hello = await Runner.run(greeter, body.history)
    # ok: client-message-roles-with-tools-py
    single = await Runner.run(billing_agent, body.message)
    return {"r": result.final_output, "s": bool(streamed), "h": hello.final_output, "x": single.final_output}


# ---- pydantic-ai -----------------------------------------------------------------------------


@app.post("/pydantic-ai")
async def pydantic_ai_chat(body: Chat):
    history = ModelMessagesTypeAdapter.validate_python(body.history)
    # ruleid: client-message-roles-with-tools-py
    result = await support.run(body.message, message_history=history)
    # ok: client-message-roles-with-tools-py
    hello = await plain_agent.run(body.message, message_history=history)
    return {"r": result.output, "h": hello.output}


# ---- Request built as one dict, then spread --------------------------------------------------

BEDROCK_BASE = {"modelId": "anthropic.claude-sonnet-5-5-v1:0", "inferenceConfig": {"maxTokens": 400}}


@app.post("/bedrock-request")
async def bedrock_request(body: Chat):
    request = {**BEDROCK_BASE, "toolConfig": TOOL_CONFIG, "messages": body.history}
    # ruleid: client-message-roles-with-tools-py
    reply = runtime.converse(**request)
    user_turns = [turn for turn in body.history if turn["role"] == "user"]
    filtered = {**BEDROCK_BASE, "toolConfig": TOOL_CONFIG, "messages": user_turns}
    # ok: client-message-roles-with-tools-py
    checked = runtime.converse(**filtered)
    plain = {**BEDROCK_BASE, "messages": body.history}
    # ok: client-message-roles-with-tools-py
    chat_only = runtime.converse(**plain)
    return {"r": reply["output"], "c": checked["output"], "p": chat_only["output"]}


@app.post("/bedrock-request/stream")
async def bedrock_request_stream(body: Chat):
    request = {"modelId": "anthropic.claude-sonnet-5-5-v1:0", "messages": body.history, "toolConfig": TOOL_CONFIG}
    # ruleid: client-message-roles-with-tools-py
    return runtime.converse_stream(**request)
