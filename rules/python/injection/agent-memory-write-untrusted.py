import queue

import httpx
import requests
from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from langgraph.store.base import BaseStore, PutOp
from letta_client import Letta
from mcp import ClientSession
from mcp.server.lowlevel import Server
from mem0 import AsyncMemory, Memory, MemoryClient
from openai import OpenAI
from sqlalchemy.orm import Session
from tavily import TavilyClient
from zep_cloud import Message
from zep_cloud.client import Zep

from .models import Ticket

api = FastAPI()
llm = ChatOpenAI(model="gpt-5")
oai = OpenAI()
memory = Memory.from_config({"vector_store": {"provider": "qdrant"}})
platform = MemoryClient()
letta = Letta(base_url="http://letta.internal.invalid:8283")
zep = Zep()
tavily = TavilyClient()
vector_store = None
engine = None
lowlevel = Server("notes")

# ---- mem0 ----------------------------------------------------------------------------------


@api.post("/research/remember")
def remember_sources(topic: str):
    docs = vector_store.as_retriever().invoke(topic)
    notes = "\n".join(d.page_content for d in docs)
    # ruleid: agent-memory-write-untrusted
    memory.add(notes, agent_id="researcher")


@api.post("/links/save")
def save_link(url: str, user_id: str):
    page = requests.get(url, timeout=10).text
    # ruleid: agent-memory-write-untrusted
    platform.add([{"role": "user", "content": page}], user_id=user_id)


def digest_page(url: str, user_id: str):
    page = httpx.get(url).text
    summary = llm.invoke(f"Summarize this page for later: {page}")
    # A model's summary of the page carries what the page told it to say.
    # ruleid: agent-memory-write-untrusted
    memory.add(summary.content, user_id=user_id, infer=False)


def digest_with_openai(url: str, user_id: str):
    body = httpx.get(url).text
    resp = oai.chat.completions.create(model="gpt-5", messages=[{"role": "user", "content": body}])
    # ruleid: agent-memory-write-untrusted
    memory.add(resp.choices[0].message.content, user_id=user_id)


async def remember_async(url: str, scope: dict):
    mem = await AsyncMemory.from_config({"llm": {"provider": "openai"}})
    async with httpx.AsyncClient() as client:
        page = (await client.get(url)).text
    # ruleid: agent-memory-write-untrusted
    await mem.add(page, **scope)


def refresh_memory(memory_id: str, url: str):
    page = requests.get(url).text
    # ruleid: agent-memory-write-untrusted
    memory.update(memory_id, text=page)


def remember_search(query: str, user_id: str):
    hits = tavily.search(query)
    # ruleid: agent-memory-write-untrusted
    platform.add(messages=[{"role": "user", "content": str(hits)}], user_id=user_id)


@api.post("/chat")
def chat(message: str, user_id: str):
    answer = llm.invoke(message)
    # The user's own message and the model's reply to it: mem0's normal use.
    # ok: agent-memory-write-untrusted
    memory.add([{"role": "user", "content": message}, {"role": "assistant", "content": answer.content}], user_id=user_id)


def remember_screened(url: str, user_id: str):
    page = requests.get(url).text
    clean = sanitize_for_memory(page)
    # ok: agent-memory-write-untrusted
    memory.add(clean, user_id=user_id)


def remember_checked(url: str, user_id: str):
    page = requests.get(url).text
    if not is_safe_to_store(page):
        return
    # ok: agent-memory-write-untrusted
    memory.add(page, user_id=user_id)


def remember_count(topic: str, user_id: str):
    docs = vector_store.similarity_search(topic)
    # ok: agent-memory-write-untrusted
    memory.add(f"Looked up {len(docs)} documents about {topic}", user_id=user_id)


def recall(url: str, user_id: str):
    page = requests.get(url).text
    # Searching memory with the page doesn't store it.
    # ok: agent-memory-write-untrusted
    return memory.search(page, filters={"user_id": user_id})


def remember_with_source(question: str, url: str, user_id: str):
    title = requests.get(url).text[:80]
    # ok: agent-memory-write-untrusted
    memory.add(question, user_id=user_id, metadata={"page_title": title})


# A value that starts with a parenthesized expression and then a method call, assigned and then
# cut: OpenGrep 1.30.2 dropped every finding in this file on it before the slice sources
# skipped such values.
def remember_trimmed_page(url: str, user_id: str):
    resp = requests.get(url)
    page = (resp.text or "").strip()
    # ruleid: agent-memory-write-untrusted
    memory.add(page[:4000], user_id=user_id)


seen_pages: set = set()


def mark_seen(url: str):
    page = requests.get(url).text
    # A set and an ORM session have add() too.
    # ok: agent-memory-write-untrusted
    seen_pages.add(page)
    with Session(engine) as session:
        # ok: agent-memory-write-untrusted
        session.add(Ticket(body=page))


def ticket_status_note(ticket_id: int, user_id: str):
    with Session(engine) as session:
        ticket = session.get(Ticket, ticket_id)
        # ok: agent-memory-write-untrusted
        memory.add(f"Ticket {ticket_id} is {ticket.status}", user_id=user_id)


# ---- LangGraph store -----------------------------------------------------------------------


async def save_tool_result(session: ClientSession, store: BaseStore, user_id: str):
    result = await session.call_tool("fetch_issue", {"id": 42})
    # ruleid: agent-memory-write-untrusted
    await store.aput(("issues", user_id), "latest", {"text": result.content[0].text})


def remember_ticket(store: BaseStore, ticket_id: int):
    with Session(engine) as session:
        ticket = session.get(Ticket, ticket_id)
    # ruleid: agent-memory-write-untrusted
    store.put(("tickets",), str(ticket_id), {"summary": ticket.body})


def batch_save(store: BaseStore, url: str):
    page = requests.get(url).text
    # ruleid: agent-memory-write-untrusted
    store.batch([PutOp(("pages",), url, {"content": page})])


def remember_vendor_page(runtime, vendor: str, url: str):
    namespace = ("vendors", vendor)
    page = httpx.get(url).text
    # ruleid: agent-memory-write-untrusted
    runtime.store.put(namespace, "status_page", value={"text": page})


work = queue.Queue()


def enqueue(url: str, cache_store):
    page = requests.get(url).text
    # A queue's put, and a key-value store's put(key, value).
    # ok: agent-memory-write-untrusted
    work.put(page)
    # ok: agent-memory-write-untrusted
    cache_store.put(url, page)


@lowlevel.call_tool()
async def handle_call(name: str, arguments: dict):
    # The low-level server's decorator is not a client call.
    # ok: agent-memory-write-untrusted
    memory.add(arguments["note"], user_id=arguments["user"])


# ---- Letta ---------------------------------------------------------------------------------


def pin_ticket(agent_id: str, ticket_id: int):
    with Session(engine) as session:
        ticket = session.get(Ticket, ticket_id)
        letta.agents.blocks.update(
            "customer",
            agent_id=agent_id,
            # ruleid: agent-memory-write-untrusted
            value=ticket.body,
        )


def archive_search(agent_id: str, query: str):
    hits = tavily.search(query)
    # ruleid: agent-memory-write-untrusted
    letta.agents.passages.create(agent_id, text=str(hits["results"]))


def new_block(url: str):
    page = requests.get(url).text
    # ruleid: agent-memory-write-untrusted
    return letta.blocks.create(label="vendor_notes", value=page)


def pin_status(agent_id: str, ticket_id: int):
    with Session(engine) as session:
        ticket = session.get(Ticket, ticket_id)
        # ok: agent-memory-write-untrusted
        letta.agents.blocks.update("status", agent_id=agent_id, value=ticket.status)


# ---- Zep -----------------------------------------------------------------------------------


def graph_page(user_id: str, url: str):
    page = requests.get(url).text
    # ruleid: agent-memory-write-untrusted
    zep.graph.add(user_id=user_id, type="text", data=page)


def graph_episode(graph_uuid: str, url: str):
    page = httpx.get(url).text
    # ruleid: agent-memory-write-untrusted
    zep.graph.episode.add(graph_uuid, data=page, type="text")


def thread_page(thread_id: str, url: str):
    page = requests.get(url).text
    # ruleid: agent-memory-write-untrusted
    zep.thread.add_messages(thread_id, messages=[Message(role="user", content=page)])


def thread_user_turn(thread_id: str, message: str):
    # ok: agent-memory-write-untrusted
    zep.thread.add_messages(thread_id, messages=[Message(role="user", content=message)])
