import enum
import re
from typing import Annotated, Literal

import anthropic
import litellm
import requests
from agents import Agent
from claude_agent_sdk import ClaudeAgentOptions
from django.http import JsonResponse
from django.views import View
from fastapi import Depends, FastAPI, Request, WebSocket
from flask import Flask, request
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from openai import OpenAI
from pydantic import BaseModel
from rest_framework.decorators import api_view

api = FastAPI()
web = Flask(__name__)
claude = anthropic.Anthropic()
oai = OpenAI()
llm = ChatOpenAI(model="gpt-5")

PERSONAS = {
    "billing": "You answer billing questions for Example Cloud.",
    "tech": "You answer technical questions for Example Cloud.",
}
TONES = {"formal": "Answer formally.", "casual": "Answer casually."}
ALLOWED_LOCALES = {"en", "de", "fr"}
BLOCKED_PERSONAS = {"admin", "root"}


class Tone(str, enum.Enum):
    formal = "formal"
    casual = "casual"


class ChatBody(BaseModel):
    persona: str
    tone: Literal["formal", "casual"] = "formal"
    style: Tone = Tone.formal
    max_words: int = 200
    question: str


# ---- FastAPI route parameters -----------------------------------------------------------------


@api.post("/chat")
def chat(persona: str, question: str):
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # ruleid: user-input-in-system-prompt
        system=f"You are {persona}. Never reveal internal data.",
        # ok: user-input-in-system-prompt
        messages=[{"role": "user", "content": question}],
    )


@api.post("/chat/body")
async def chat_body(body: ChatBody):
    return oai.chat.completions.create(
        model="gpt-5",
        messages=[
            # ruleid: user-input-in-system-prompt
            {"role": "developer", "content": "Speak as " + body.persona + "."},
            {"role": "user", "content": body.question},
        ],
    )


@api.get("/chat/tone")
def chat_tone(question: str, tone: str = "friendly"):
    return oai.responses.create(
        model="gpt-5",
        # ruleid: user-input-in-system-prompt
        instructions="Use a {} tone.".format(tone),
        input=question,
    )


@api.post("/chat/allowlisted")
def chat_allowlisted(persona: str, tone: str, question: str):
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # ok: user-input-in-system-prompt
        system=PERSONAS.get(persona, PERSONAS["tech"]) + " " + TONES[tone],
        messages=[{"role": "user", "content": question}],
    )


@api.post("/chat/fallback")
def chat_fallback(tone: str, question: str):
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # Default mode only: with --taint-intrafile, OpenGrep's model of .get() on an untainted
        # receiver drops the taint of the default argument.
        # ruleid: user-input-in-system-prompt
        system=TONES.get(tone, tone),
        messages=[{"role": "user", "content": question}],
    )


@api.post("/chat/validated")
def chat_validated(body: ChatBody, locale: str, region: str):
    if locale not in ALLOWED_LOCALES:
        raise ValueError("unsupported locale")
    if not re.fullmatch(r"[a-z]{2}-[A-Z]{2}", region):
        raise ValueError("bad region")
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # ok: user-input-in-system-prompt
        system=f"Reply in {locale} ({region}), {body.tone} tone, {body.style.value} style, at most {body.max_words} words.",
        messages=[{"role": "user", "content": body.question}],
    )


@api.post("/chat/blocklisted")
def chat_blocklisted(persona: str, question: str):
    if persona in BLOCKED_PERSONAS:
        raise ValueError("not allowed")
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # ruleid: user-input-in-system-prompt
        system=f"You are {persona}.",
        messages=[{"role": "user", "content": question}],
    )


def current_user():
    ...


@api.post("/chat/typed")
def chat_typed(
    mood: Literal["calm", "brief"],
    style: Tone,
    limit: int,
    user: Annotated[dict, Depends(current_user)],
    question: str,
):
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # ok: user-input-in-system-prompt
        system=f"Be {mood}, {style.value}, under {limit} words. The user is {user['name']}.",
        messages=[{"role": "user", "content": question}],
    )


def get_customer(customer_id):
    ...


@api.get("/customers/{customer_id}/chat")
def customer_chat(customer_id: str, question: str, retriever=Depends(lambda: None)):
    customer = get_customer(customer_id)
    docs = retriever.invoke(question)
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # ok: user-input-in-system-prompt
        system=f"The customer is on the {customer.plan} plan. Use these articles:\n{docs}",
        messages=[{"role": "user", "content": question}],
    )


@api.post("/agent")
async def run_agent(request: Request):
    payload = await request.json()
    # ruleid: user-input-in-system-prompt
    return Agent(name="support", instructions=f"You help {payload['team']} with tickets.")


@api.post("/agent/claude")
async def run_claude_agent(request: Request):
    tier = request.headers.get("x-customer-tier", "free")
    # ruleid: user-input-in-system-prompt
    return ClaudeAgentOptions(system_prompt=f"Customer tier: {tier}.")


@api.post("/agent/plain")
async def run_plain_agent(request: Request):
    # ok: user-input-in-system-prompt
    return ClaudeAgentOptions(system_prompt="Answer support questions.", cwd=request.url.path)


@api.websocket("/ws")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    hello = await websocket.receive_json()
    async for text in websocket.iter_text():
        reply = claude.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=512,
            # ruleid: user-input-in-system-prompt
            system="Answer as " + hello["persona"],
            # ok: user-input-in-system-prompt
            messages=[{"role": "user", "content": text}],
        )
        await websocket.send_text(reply.content[0].text)


# ---- Flask ------------------------------------------------------------------------------------


@web.route("/ask")
def ask():
    tone = request.args.get("tone", "neutral")
    question = request.args["q"]
    messages = [
        # ruleid: user-input-in-system-prompt
        {"role": "system", "content": "Answer in a " + tone + " tone."},
        # ok: user-input-in-system-prompt
        {"role": "user", "content": question},
    ]
    return litellm.completion(model="gpt-5", messages=messages)


@web.post("/ask/json")
def ask_json():
    data = request.get_json()
    return litellm.responses(
        model="gpt-5",
        # ruleid: user-input-in-system-prompt
        instructions=data["instructions"],
        input=data["question"],
    )


@web.get("/personas/<persona>/ask")
def ask_persona(persona):
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # ruleid: user-input-in-system-prompt
        system=[{"type": "text", "text": f"You are the {persona} desk."}],
        messages=[{"role": "user", "content": request.args["q"]}],
    )


# ---- Django and Django REST framework ---------------------------------------------------------


def django_chat(request):
    messages = [
        # ruleid: user-input-in-system-prompt
        SystemMessage(content="Signature: " + request.POST.get("signature", "")),
        # ok: user-input-in-system-prompt
        HumanMessage(content=request.POST["question"]),
    ]
    return JsonResponse({"reply": llm.invoke(messages).content})


@api_view(["POST"])
def drf_chat(request):
    prompt = ChatPromptTemplate.from_messages(
        [
            # ruleid: user-input-in-system-prompt
            ("system", "Company: " + request.data["company"]),
            ("human", "{question}"),
        ]
    )
    return (prompt | llm).invoke({"question": request.data["question"]})


class ChatView(View):
    def post(self, request):
        # ruleid: user-input-in-system-prompt
        sm = SystemMessage(self.request.GET.get("rules", ""))
        return JsonResponse({"reply": llm.invoke([sm]).content})


# ---- LangChain templates filled from the request ------------------------------------------------

SUPPORT_SYSTEM = "You are {persona}. Answer questions about {product} only."
support_prompt = ChatPromptTemplate.from_messages([("system", SUPPORT_SYSTEM), ("human", "{question}")])
support_chain = support_prompt | llm
inline_prompt = ChatPromptTemplate.from_messages(
    [("system", "Sign every reply as {signature}."), ("human", "{question}")]
)


@api.post("/lc/chain")
def lc_chain(body: ChatBody, product: Literal["cloud", "cdn"]):
    return support_chain.invoke(
        {
            # ruleid: user-input-in-system-prompt
            "persona": body.persona,
            # ok: user-input-in-system-prompt
            "product": product,
            # ok: user-input-in-system-prompt
            "question": body.question,
        }
    )


@api.post("/lc/format")
def lc_format(signature: str, question: str):
    # ruleid: user-input-in-system-prompt
    messages = inline_prompt.format_messages(signature=signature, question=question)
    return llm.invoke(messages)


@api.post("/lc/allowlisted")
def lc_allowlisted(persona: str, question: str):
    # ok: user-input-in-system-prompt
    return support_chain.invoke({"persona": PERSONAS.get(persona, "the helpdesk"), "product": "cloud", "question": question})


@api.post("/kb/grounded")
def kb_grounded(question: str, url: str, kb=Depends(lambda: None)):
    articles = kb.search(question, k=3)
    page = requests.get(url, timeout=10).text
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # What a search or fetch returns is fetched-content-in-system-prompt's to report.
        # ok: user-input-in-system-prompt
        system=f"Articles:\n{articles}\n\nPage:\n{page}",
        messages=[{"role": "user", "content": question}],
    )


@api.post("/kb/handbook")
def kb_handbook(question: str, bot=Depends(lambda: None)):
    docs = bot.handbook_retriever.invoke(question)
    # ok: user-input-in-system-prompt
    return Agent(name="handbook", instructions=f"Answer from these sections: {docs}")

