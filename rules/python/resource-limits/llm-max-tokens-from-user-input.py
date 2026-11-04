import asyncio
from typing import Annotated, Optional

import anthropic
import httpx
import litellm
from agents import Agent, Runner
from crewai import Agent as CrewAgent
from fastapi import FastAPI, Query
from flask import Flask, request
from google import genai
from google.genai import types
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from openai import OpenAI
from pydantic import BaseModel, Field, conint, field_validator
from smolagents import CodeAgent

from . import schemas

api = FastAPI()
app = Flask(__name__)
client = OpenAI()
claude = anthropic.Anthropic()
gclient = genai.Client()

MAX_TOKENS = 2048
PLAN_LIMITS = {"free": 512, "pro": 4096}
ALLOWED_LENGTHS = {256, 512, 1024}


class AskBody(BaseModel):
    question: str
    max_tokens: int = 512
    n: int = 1
    variants: int = 1


class BoundedAsk(BaseModel):
    question: str
    max_tokens: int = Field(512, ge=1, le=4096)
    n: conint(ge=1, le=3) = 1
    steps: Annotated[int, Field(le=20)] = 10


class ValidatedAsk(BaseModel):
    question: str
    max_tokens: int = 512

    @field_validator("max_tokens")
    @classmethod
    def cap_tokens(cls, v):
        return min(v, MAX_TOKENS)


# ---- OpenAI -----------------------------------------------------------------------------------

@api.post("/ask")
def openai_chat(body: AskBody):
    return client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": body.question}],
        # ruleid: llm-max-tokens-from-user-input
        max_completion_tokens=body.max_tokens,
        # ruleid: llm-max-tokens-from-user-input
        n=body.n,
    )


@app.post("/flask/ask")
def openai_flask():
    tokens = int(request.args.get("max_tokens", 512))
    # ruleid: llm-max-tokens-from-user-input
    return client.responses.create(model="gpt-5-mini", input="hi", max_output_tokens=tokens)


@api.get("/summary")
def openai_query_param(topic: str, max_tokens: int = 512):
    # ruleid: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=max_tokens)


@api.get("/summary/bounded")
def openai_query_param_bounded(topic: str, max_tokens: int = Query(512, ge=1, le=4096)):
    # ok: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=max_tokens)


@api.get("/summary/annotated")
def openai_query_param_annotated(max_tokens: Annotated[int, Query(le=4096)] = 512):
    # ok: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=max_tokens)


@api.post("/ask/min")
def openai_min(body: AskBody):
    # ok: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=min(body.max_tokens, MAX_TOKENS))


@api.post("/ask/checked")
def openai_checked(body: AskBody):
    if body.max_tokens > MAX_TOKENS:
        raise ValueError("max_tokens too large")
    # ok: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=body.max_tokens)


@api.post("/ask/lower-bound-only")
def openai_lower_bound(body: AskBody):
    if body.max_tokens < 1:
        raise ValueError("max_tokens must be positive")
    # ruleid: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=body.max_tokens)


@api.post("/ask/ternary")
def openai_ternary(body: AskBody):
    tokens = body.max_tokens if body.max_tokens <= MAX_TOKENS else MAX_TOKENS
    # ok: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=tokens)


@api.post("/ask/bounded")
def openai_bounded_model(body: BoundedAsk):
    # ok: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=body.max_tokens, n=body.n)


@api.post("/ask/validated")
def openai_validated_model(body: ValidatedAsk):
    # ok: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=body.max_tokens)


@api.post("/ask/plan")
def openai_plan_table(plan: str):
    # ok: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=PLAN_LIMITS[plan])


@app.post("/flask/allowlisted")
def openai_allowlisted():
    tokens = int(request.form["max_tokens"])
    if tokens not in ALLOWED_LENGTHS:
        return "bad length", 400
    # ok: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=tokens)


@api.post("/ask/server-default")
def openai_server_value(body: AskBody):
    # ok: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[{"role": "user", "content": body.question}], max_tokens=MAX_TOKENS)


@api.post("/ask/kwargs")
def openai_kwargs(body: AskBody):
    # ruleid: llm-max-tokens-from-user-input
    params = {"model": "gpt-5-mini", "max_tokens": body.max_tokens}
    return client.chat.completions.create(messages=[], **params)


@api.post("/ask/kwargs-subscript")
def openai_kwargs_subscript(body: AskBody):
    params = {"model": "gpt-5-mini"}
    # ruleid: llm-max-tokens-from-user-input
    params["max_completion_tokens"] = body.max_tokens
    return client.chat.completions.create(messages=[], **params)


@api.post("/ask/echo")
def echo_settings(body: AskBody):
    # ok: llm-max-tokens-from-user-input
    return {"max_tokens": body.max_tokens, "question": body.question}


# ---- Anthropic, LiteLLM, raw HTTP --------------------------------------------------------------

@api.post("/claude")
def anthropic_messages(body: AskBody):
    # ruleid: llm-max-tokens-from-user-input
    return claude.messages.create(model="claude-sonnet-4-5", max_tokens=body.max_tokens, messages=[])


@api.post("/claude/stream")
async def anthropic_stream(body: BoundedAsk):
    # ok: llm-max-tokens-from-user-input
    with claude.messages.stream(model="claude-sonnet-4-5", max_tokens=body.max_tokens, messages=[]) as s:
        return s.get_final_text()


@app.post("/litellm")
def litellm_call():
    data = request.get_json()
    # ruleid: llm-max-tokens-from-user-input
    return litellm.completion(model="gpt-5-mini", messages=[], max_tokens=data["max_tokens"])


@app.post("/raw")
def raw_http():
    data = request.get_json()
    # ruleid: llm-max-tokens-from-user-input
    return httpx.post("https://api.example.invalid/v1/messages", json={"model": "m", "max_tokens": data.get("max_tokens")})


# ---- Google, LangChain ----------------------------------------------------------------------

@api.post("/gemini")
def gemini_call(body: AskBody):
    return gclient.models.generate_content(
        model="gemini-2.5-flash",
        contents=body.question,
        # ruleid: llm-max-tokens-from-user-input
        config=types.GenerateContentConfig(max_output_tokens=body.max_tokens),
    )


@api.post("/gemini/dict")
def gemini_dict(body: AskBody):
    # ruleid: llm-max-tokens-from-user-input
    return gclient.models.generate_content(model="gemini-2.5-flash", contents="x", config={"max_output_tokens": body.max_tokens})


@api.post("/langchain")
def langchain_model(body: AskBody):
    # ruleid: llm-max-tokens-from-user-input
    llm = ChatOpenAI(model="gpt-5-mini", max_tokens=body.max_tokens)
    return llm.invoke(body.question)


@api.post("/langchain/bind")
def langchain_bind(body: AskBody):
    llm = ChatAnthropic(model="claude-sonnet-4-5")
    # ruleid: llm-max-tokens-from-user-input
    return llm.bind(max_tokens=body.max_tokens).invoke(body.question)


# ---- Agent step caps and loops --------------------------------------------------------------

@api.post("/agent")
async def agent_run(body: AskBody):
    agent = Agent(name="helper", instructions="Answer briefly.")
    # ruleid: llm-max-tokens-from-user-input
    return await Runner.run(agent, body.question, max_turns=body.variants)


@api.post("/crew")
def crew_agent(body: AskBody):
    # ruleid: llm-max-tokens-from-user-input
    return CrewAgent(role="r", goal="g", backstory="b", max_iter=body.variants)


@api.post("/smol")
def smol_agent(body: BoundedAsk):
    # ok: llm-max-tokens-from-user-input
    return CodeAgent(tools=[], model=None, max_steps=body.steps)


@api.post("/graph")
def graph_run(body: AskBody, graph=None):
    # ruleid: llm-max-tokens-from-user-input
    return graph.invoke({"question": body.question}, {"recursion_limit": body.variants})


@api.post("/variants")
def variant_loop(body: AskBody):
    drafts = []
    # ruleid: llm-max-tokens-from-user-input
    for _ in range(body.variants):
        drafts.append(client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=256))
    return drafts


@api.post("/variants/gather")
async def variant_gather(body: AskBody):
    # ruleid: llm-max-tokens-from-user-input
    return await asyncio.gather(*(claude.messages.create(model="m", max_tokens=256, messages=[]) for _ in range(body.variants)))


@api.post("/variants/capped")
def variant_loop_capped(body: AskBody):
    drafts = []
    # ok: llm-max-tokens-from-user-input
    for _ in range(min(body.variants, 3)):
        drafts.append(client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=256))
    return drafts


@api.post("/pages")
def page_loop(body: AskBody):
    out = []
    # ok: llm-max-tokens-from-user-input
    for i in range(body.variants):
        out.append(i * 2)
    return out


# ---- Other request shapes and caps ------------------------------------------------------------

def clamp(value, low, high):
    return max(low, min(value, high))


@app.post("/flask/typed")
def flask_typed_arg():
    tokens = request.args.get("max_tokens", 512, type=int)
    # ruleid: llm-max-tokens-from-user-input
    return claude.messages.create(model="claude-sonnet-4-5", max_tokens=tokens, messages=[])


@app.post("/flask/clamped")
def flask_clamped():
    tokens = clamp(request.args.get("max_tokens", 512, type=int), 1, MAX_TOKENS)
    # ok: llm-max-tokens-from-user-input
    return claude.messages.create(model="claude-sonnet-4-5", max_tokens=tokens, messages=[])


@app.post("/flask/range-checked")
def flask_range_checked():
    tokens = request.get_json()["max_tokens"]
    if not 1 <= tokens <= MAX_TOKENS:
        return "bad max_tokens", 400
    # ok: llm-max-tokens-from-user-input
    return claude.messages.create(model="claude-sonnet-4-5", max_tokens=tokens, messages=[])


@api.websocket("/ws")
async def ws_chat(websocket):
    msg = await websocket.receive_json()
    # ruleid: llm-max-tokens-from-user-input
    stream = await litellm.acompletion(model="gpt-5-mini", messages=[], max_tokens=msg["max_tokens"], stream=True)
    async for chunk in stream:
        await websocket.send_json(chunk)


@api.post("/retry")
def retry_loop(body: AskBody):
    # ruleid: llm-max-tokens-from-user-input
    for attempt in range(1, body.variants):
        try:
            return client.responses.create(model="gpt-5-mini", input=body.question)
        except Exception:
            continue
    return None


@api.post("/ask/optional-cap")
def openai_optional_cap(body: AskBody):
    opts = {"model": "gpt-5-mini", "temperature": 0.3}
    if body.max_tokens:
        # ruleid: llm-max-tokens-from-user-input
        opts["max_tokens"] = body.max_tokens
    return client.chat.completions.create(messages=[], **opts)


@api.post("/ask/imported-model")
def openai_imported_model(body: schemas.DraftRequest):
    # The model is declared in another module, which may bound the field.
    # ok: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=body.max_tokens)


@app.post("/flask/imported-model")
def flask_imported_model():
    req = schemas.DraftRequest.model_validate(request.get_json())
    # ok: llm-max-tokens-from-user-input
    return client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=req.max_tokens)


# ---- while loops ------------------------------------------------------------------------------

@api.post("/retry/while")
def retry_while(body: AskBody):
    attempts = 0
    # ruleid: llm-max-tokens-from-user-input
    while attempts < body.variants:
        attempts += 1
        reply = claude.messages.create(model="claude-sonnet-4-5", max_tokens=256, messages=[])
        if reply.stop_reason == "end_turn":
            return reply
    return None


@api.post("/drafts/while")
def drafts_while(body: AskBody):
    drafts = []
    # ruleid: llm-max-tokens-from-user-input
    while len(drafts) < body.n:
        drafts.append(client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=256))
    return drafts


@api.post("/retry/while-capped")
def retry_while_capped(body: AskBody):
    limit = min(body.variants, 3)
    attempts = 0
    # ok: llm-max-tokens-from-user-input
    while attempts < limit:
        attempts += 1
        reply = claude.messages.create(model="claude-sonnet-4-5", max_tokens=256, messages=[])
        if reply.stop_reason == "end_turn":
            return reply
    return None


@api.post("/retry/while-clamped")
def retry_while_clamped(body: AskBody):
    limit = clamp(body.variants, 1, 3)
    drafts = []
    # ok: llm-max-tokens-from-user-input
    while len(drafts) < limit:
        drafts.append(client.chat.completions.create(model="gpt-5-mini", messages=[], max_tokens=256))
    return drafts


@api.post("/retry/while-true")
def retry_while_true(body: AskBody):
    attempts = 0
    # ok: llm-max-tokens-from-user-input
    while True:
        attempts += 1
        reply = claude.messages.create(model="claude-sonnet-4-5", max_tokens=256, messages=[])
        if reply.stop_reason == "end_turn" or attempts >= 3:
            return reply


@api.post("/pages/while")
def pages_while(body: AskBody):
    out = []
    # ok: llm-max-tokens-from-user-input
    while len(out) < body.variants:
        out.append(len(out) * 2)
    return out
