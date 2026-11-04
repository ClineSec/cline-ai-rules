import csv
from urllib.request import urlopen

import aiohttp
import anthropic
import asyncpg
import chromadb
import httpx
import requests
import serpapi
from agents import Agent
from bs4 import BeautifulSoup
from claude_agent_sdk import ClaudeAgentOptions
from ddgs import DDGS
from exa_py import Exa
from fastapi import FastAPI
from googleapiclient.discovery import build
from firecrawl import Firecrawl
from jinja2 import Environment, FileSystemLoader
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools import BraveSearch, DuckDuckGoSearchRun
from langchain_community.utilities import BingSearchAPIWrapper, SerpAPIWrapper
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_openai import ChatOpenAI
from llama_index.core import VectorStoreIndex
from openai import OpenAI
from playwright.async_api import async_playwright
from pydantic_ai import Agent as PydanticAgent
from qdrant_client import QdrantClient
from serpapi import GoogleSearch
from sqlalchemy import select
from sqlalchemy.orm import Session
from tavily import TavilyClient

from .models import Comment, Message, TenantSettings, Ticket

api = FastAPI()
claude = anthropic.Anthropic()
oai = OpenAI()
llm = ChatOpenAI(model="gpt-5")
vector_store = None
li_index: VectorStoreIndex = None
engine = None

# ---- Retrieved documents ----------------------------------------------------------------------


@api.post("/kb/ask")
def kb_ask(question: str):
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    docs = retriever.invoke(question)
    context = "\n\n".join(d.page_content for d in docs)
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1024,
        # ruleid: fetched-content-in-system-prompt
        system=f"Answer from these articles only:\n{context}",
        # ok: fetched-content-in-system-prompt
        messages=[{"role": "user", "content": question}],
    )


@api.post("/kb/ask/grounded")
def kb_ask_grounded(question: str):
    hits = vector_store.similarity_search(question, k=3)
    return oai.chat.completions.create(
        model="gpt-5",
        messages=[
            # ruleid: fetched-content-in-system-prompt
            {"role": "developer", "content": "Use this context: " + hits[0].page_content},
            {"role": "user", "content": question},
        ],
    )


@api.post("/kb/ask/separated")
def kb_ask_separated(question: str):
    docs = vector_store.similarity_search(question, k=3)
    articles = "\n\n".join(d.page_content for d in docs)
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1024,
        # ok: fetched-content-in-system-prompt
        system=f"Answer from the articles in the user turn. {len(docs)} articles were found.",
        messages=[
            # ok: fetched-content-in-system-prompt
            {"role": "user", "content": f"<articles>\n{articles}\n</articles>\n\n{question}"},
        ],
    )


@api.post("/kb/llamaindex")
def kb_llamaindex(question: str):
    nodes = li_index.as_retriever(similarity_top_k=3).retrieve(question)
    notes = "\n".join(n.get_content() for n in nodes)
    # ruleid: fetched-content-in-system-prompt
    return llm.invoke([SystemMessage(content=f"Relevant notes:\n{notes}"), HumanMessage(content=question)])


async def answer_with_agent(question: str, doc_retriever):
    found = await doc_retriever.ainvoke(question)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="kb", instructions="Ground every answer in: " + str(found))


# ---- Loaders, web search, and fetched pages ----------------------------------------------------


def summarize_page(url: str):
    pages = WebBaseLoader(url).load()
    # ruleid: fetched-content-in-system-prompt
    return ClaudeAgentOptions(system_prompt=f"Summarize this page for the user:\n{pages[0].page_content}")


def research(topic: str):
    tavily = TavilyClient()
    results = tavily.search(topic, max_results=5)
    snippets = "\n".join(r["content"] for r in results["results"])
    return oai.responses.create(
        model="gpt-5",
        # ruleid: fetched-content-in-system-prompt
        instructions=f"Base your answer on these search results:\n{snippets}",
        input=topic,
    )


def describe_link(url: str):
    page = requests.get(url, timeout=10)
    text = BeautifulSoup(page.text, "html.parser").get_text()
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # ruleid: fetched-content-in-system-prompt
        system="You describe web pages. Page text:\n" + text[:8000],
        messages=[{"role": "user", "content": "Describe it."}],
    )


async def describe_link_async(link_url: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(link_url)
    return oai.chat.completions.create(
        model="gpt-5",
        messages=[
            # ruleid: fetched-content-in-system-prompt
            {"role": "system", "content": f"Page:\n{resp.text}"},
            {"role": "user", "content": "Summarize."},
        ],
    )


async def describe_link_aiohttp(page_url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(page_url) as resp:
            html = await resp.text()
    # ruleid: fetched-content-in-system-prompt
    return ClaudeAgentOptions(system_prompt="Page HTML:\n" + html)


def describe_feed(feed_url: str):
    raw = urlopen(feed_url).read().decode("utf-8")
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="feeds", instructions=f"Latest feed:\n{raw}")


async def describe_rendered(url: str):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        visible = await page.inner_text("main")
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="browse", instructions="Rendered page:\n" + visible)


def fetch_page(url):
    ...


def describe_with_helper(url: str):
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="pages", instructions="Page:\n" + fetch_page(url))


def status_banner(status_url: str):
    status = requests.get(status_url).json()
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=256,
        # ok: fetched-content-in-system-prompt
        system=f"Service status: {status['state']}. Open incidents: {status['open_count']}.",
        messages=[{"role": "user", "content": "Any outages?"}],
    )


def incident_brief(status_url: str):
    status = requests.get(status_url).json()
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=256,
        # ruleid: fetched-content-in-system-prompt
        system="Current incident: " + status["description"],
        messages=[{"role": "user", "content": "What is happening?"}],
    )


async def runbook_from_tool(session, service: str):
    # An MCP server's tool result: the server's operator wrote it.
    result = await session.call_tool("get_runbook", {"service": service})
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # ruleid: fetched-content-in-system-prompt
        system=f"Follow this runbook:\n{result.content[0].text}",
        messages=[{"role": "user", "content": "The service is down."}],
    )


async def tool_count(session, service: str):
    result = await session.call_tool("list_alerts", {"service": service})
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # ok: fetched-content-in-system-prompt
        system=f"There are {len(result.content)} open alerts.",
        messages=[{"role": "user", "content": "Summarize the alerts in the attached tool output."}],
    )


# ---- Stored records ---------------------------------------------------------------------------


def ticket_assistant(ticket_id: int):
    with Session(engine) as session:
        ticket = session.get(Ticket, ticket_id)
        return claude.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=1024,
            # ruleid: fetched-content-in-system-prompt
            system=f"Ticket #{ticket.id} ({ticket.status}): {ticket.body}",
            messages=[{"role": "user", "content": "Draft a reply."}],
        )


def ticket_status(ticket_id: int):
    with Session(engine) as session:
        ticket = session.get(Ticket, ticket_id)
        return claude.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=256,
            # ok: fetched-content-in-system-prompt
            system=f"Ticket #{ticket.id} is {ticket.status}, priority {ticket.priority}.",
            messages=[{"role": "user", "content": ticket.body}],
        )


def thread_digest(ticket_id: int):
    with Session(engine) as session:
        comments = session.scalars(select(Comment).where(Comment.ticket_id == ticket_id)).all()
        history = "\n".join(f"- {c.author}: {c.text}" for c in comments)
    # ruleid: fetched-content-in-system-prompt
    return llm.invoke([("system", "Thread so far:\n" + history), ("human", "Summarize the thread.")])


def django_reply(ticket_id: int):
    ticket = Ticket.objects.select_related("customer").get(pk=ticket_id)
    return oai.responses.create(
        model="gpt-5",
        # ruleid: fetched-content-in-system-prompt
        instructions=f"Customer wrote: {ticket.subject}",
        input="Draft a reply.",
    )


def tenant_persona(tenant_id: int):
    settings = TenantSettings.objects.get(tenant_id=tenant_id)
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # ok: fetched-content-in-system-prompt
        system=settings.persona_text + "\n" + settings.description,
        messages=[{"role": "user", "content": "Hello"}],
    )


def get_ticket(ticket_id):
    ...


def get_tenant_persona(tenant_id):
    ...


def helper_reply(ticket_id: int, tenant_id: int):
    ticket = get_ticket(ticket_id)
    persona = get_tenant_persona(tenant_id)
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=512,
        # ruleid: fetched-content-in-system-prompt
        system=f"{persona.text}\n\nThe customer's last message: {ticket.last_message}",
        messages=[{"role": "user", "content": "Draft a reply."}],
    )


def helper_persona_only(tenant_id: int):
    persona = get_tenant_persona(tenant_id)
    # ok: fetched-content-in-system-prompt
    return ClaudeAgentOptions(system_prompt=persona.text)


async def pg_reply(pool: asyncpg.Pool, ticket_id: int):
    async with pool.acquire() as conn:
        body = await conn.fetchval("SELECT body FROM tickets WHERE id = $1", ticket_id)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="reply", instructions="Reply to this ticket:\n" + body)


def jinja_prompt(team: str):
    env = Environment(loader=FileSystemLoader("prompts"))
    # ok: fetched-content-in-system-prompt
    return Agent(name="team", instructions=env.get_template("system.j2").render(team=team))


def csv_glossary(path: str):
    with open(path) as fh:
        terms = {row["term"]: row["definition"] for row in csv.DictReader(fh)}
    # ok: fetched-content-in-system-prompt
    return Agent(name="glossary", instructions=f"Known terms: {', '.join(terms)}")


# ---- LangChain templates, chains, and middleware ------------------------------------------------

RAG_SYSTEM = "Answer using only this context:\n{context}"
rag_prompt = ChatPromptTemplate.from_messages([("system", RAG_SYSTEM), ("human", "{question}")])
rag_chain = rag_prompt | llm | StrOutputParser()
lcel_prompt = ChatPromptTemplate.from_messages(
    [("system", "You are the docs assistant. Context:\n{context}"), ("human", "{question}")]
)
user_turn_prompt = ChatPromptTemplate.from_messages(
    [("system", "Answer from the context in the user message."), ("human", "Context:\n{context}\n\n{question}")]
)


def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)


def rag_answer(question: str):
    docs = vector_store.similarity_search(question)
    return rag_chain.invoke(
        {
            # ruleid: fetched-content-in-system-prompt
            "context": format_docs(docs),
            # ok: fetched-content-in-system-prompt
            "question": question,
        }
    )


def rag_answer_user_turn(question: str):
    docs = vector_store.similarity_search(question)
    # ok: fetched-content-in-system-prompt
    return (user_turn_prompt | llm).invoke({"context": format_docs(docs), "question": question})


docs_retriever = vector_store.as_retriever()
lcel_chain = (
    # ruleid: fetched-content-in-system-prompt
    {"context": docs_retriever | format_docs, "question": RunnablePassthrough()}
    | lcel_prompt
    | llm
)

stuff_prompt = ChatPromptTemplate.from_messages(
    [
        # ruleid: fetched-content-in-system-prompt
        ("system", "Use the following documents to answer.\n\n{context}"),
        ("human", "{input}"),
    ]
)
combine_chain = create_stuff_documents_chain(llm, stuff_prompt)

stuff_user_prompt = ChatPromptTemplate.from_messages(
    [
        # ok: fetched-content-in-system-prompt
        ("system", "Answer from the documents in the user message."),
        ("human", "Documents:\n{context}\n\n{input}"),
    ]
)
combine_user_chain = create_stuff_documents_chain(llm, stuff_user_prompt)


@dynamic_prompt
def prompt_with_context(request: ModelRequest) -> str:
    last_query = request.state["messages"][-1].text
    retrieved = vector_store.similarity_search(last_query)
    docs_content = "\n\n".join(doc.page_content for doc in retrieved)
    # ruleid: fetched-content-in-system-prompt
    return f"You are a helpful assistant. Use the following context in your response:\n\n{docs_content}"


rag_agent = create_agent(llm, tools=[], middleware=[prompt_with_context])

support_agent = PydanticAgent("openai:gpt-5")


@support_agent.system_prompt
def kb_system_prompt() -> str:
    docs = vector_store.similarity_search("refund policy", k=2)
    # ruleid: fetched-content-in-system-prompt
    return "Refund policy excerpts:\n" + format_docs(docs)


# ---- Content cut to fit the context window --------------------------------------------------


def top_hits(question: str):
    return claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1024,
        # ruleid: fetched-content-in-system-prompt
        system=f"Context:\n{vector_store.similarity_search(question, k=10)[:3]}",
        messages=[{"role": "user", "content": question}],
    )


def short_docs(question: str):
    docs = docs_retriever.invoke(question)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="kb", instructions="Context:\n" + "\n".join(d.page_content[:500] for d in docs))


def short_page(url: str):
    resp = requests.get(url, timeout=10)
    # ruleid: fetched-content-in-system-prompt
    return ClaudeAgentOptions(system_prompt="Page:\n" + resp.text[:4000])


def short_ticket(ticket_id: int):
    with Session(engine) as session:
        ticket = session.get(Ticket, ticket_id)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="reply", instructions=f"Ticket: {ticket.body[:500]} (status {ticket.status})")


def short_thread(ticket_id: int):
    with Session(engine) as session:
        comments = session.scalars(select(Comment).where(Comment.ticket_id == ticket_id)).all()
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="thread", instructions="Thread:\n" + "\n".join(c.text[:200] for c in comments))


async def short_pg_reply(pool: asyncpg.Pool, ticket_id: int):
    async with pool.acquire() as conn:
        body = await conn.fetchval("SELECT body FROM tickets WHERE id = $1", ticket_id)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="reply", instructions="Reply to this ticket:\n" + body[:2000])


def short_local_prompt():
    with open("prompts/system.md") as fh:
        base = fh.read()
    # ok: fetched-content-in-system-prompt
    return Agent(name="kb", instructions=base[:4000])


def short_model_summary(question: str):
    reply = claude.messages.create(model="claude-sonnet-5-5", max_tokens=256, messages=[{"role": "user", "content": question}])
    summary = reply.content[0].text
    # ok: fetched-content-in-system-prompt
    return Agent(name="followup", instructions=f"Earlier summary: {summary[:300]}")


faq_prompt = ChatPromptTemplate.from_messages(
    [
        # ruleid: fetched-content-in-system-prompt
        ("system", "Answer from these FAQ entries:\n{faq_entries}"),
        ("human", "{input}"),
    ]
)
faq_chain = create_stuff_documents_chain(llm, faq_prompt, document_variable_name="faq_entries")


def strip_tags(html: str) -> str:
    ...


async def short_status(status_url: str):
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(status_url)
    page_text = strip_tags(resp.text)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="status", instructions="Status page:\n" + page_text[:6000])


def short_status_code(status_url: str):
    resp = requests.get(status_url, timeout=5)
    reason = resp.reason
    # ok: fetched-content-in-system-prompt
    return Agent(name="status", instructions=f"Status page answered {resp.status_code} " + reason[:40])


# A value that starts with a parenthesized expression and then a method call, assigned and then
# cut: OpenGrep 1.30.2 dropped every finding in this file on it ("Invalid_argument: String.sub")
# before the slice sources skipped such values.
async def short_status_trimmed(status_url: str):
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(status_url)
    page_text = (resp.text or "").strip()
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="status", instructions="Status page:\n" + page_text[:6000])


def short_build_banner(settings):
    build_sha = (settings.build_sha or "unknown").strip()
    # ok: fetched-content-in-system-prompt
    return Agent(name="status", instructions=f"You answer status questions for build {build_sha[:7]}.")


def message_header(message_id: int):
    with Session(engine) as session:
        message = session.get(Message, message_id)
        # ok: fetched-content-in-system-prompt
        return Agent(name="header", instructions=f"The message is {message.status}, sent {message.sent_at}.")


exa = Exa(api_key="fake-exa-key-for-tests")
firecrawl = Firecrawl(api_key="fc-fake-key-for-tests")
chroma = chromadb.PersistentClient(path="./chroma")
qdrant = QdrantClient(url="http://qdrant.invalid:6333")


def exa_brief(topic: str):
    results = exa.search_and_contents(topic, num_results=3, text=True)
    notes = "\n".join(r.text for r in results.results)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="brief", instructions=f"Write a brief from these sources:\n{notes}")


def firecrawl_summary(url: str):
    doc = firecrawl.scrape(url, formats=["markdown"])
    return oai.chat.completions.create(
        model="gpt-5",
        messages=[
            # ruleid: fetched-content-in-system-prompt
            {"role": "system", "content": f"Summarize this page:\n{doc.markdown}"},
            {"role": "user", "content": "Summary?"},
        ],
    )


def chroma_answer(question: str):
    collection = chroma.get_collection("handbook")
    found = collection.query(query_texts=[question], n_results=4)
    context = "\n\n".join(found["documents"][0])
    # ruleid: fetched-content-in-system-prompt
    return claude.messages.create(model="claude-sonnet-5-5", max_tokens=512, system=f"Context:\n{context}",
                                  messages=[{"role": "user", "content": question}])


def qdrant_answer(question: str, vector: list[float]):
    points = qdrant.query_points("handbook", query=vector, limit=4, with_payload=True).points
    context = "\n\n".join(p.payload["text"] for p in points)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="handbook", instructions=f"Answer from the handbook:\n{context}")


def weaviate_answer(articles, question: str):
    response = articles.query.near_text(query=question, limit=3)
    context = "\n\n".join(o.properties["body"] for o in response.objects)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="kb", instructions=f"Answer from these articles:\n{context}")


def example_lookup(examples, question: str):
    shots = examples.search(question)
    # ok: fetched-content-in-system-prompt
    return Agent(name="fewshot", instructions=f"Answer in the style of these examples: {shots}")


class ChangelogWatcher:
    def __init__(self):
        self.http = httpx.Client(timeout=10)

    def digest(self, url: str):
        resp = self.http.get(url)
        # ruleid: fetched-content-in-system-prompt
        return Agent(name="changelog", instructions=f"Summarize the latest changes:\n{resp.text}")

    def digest_short(self, feed: str):
        resp = self.http.get(feed)
        # ruleid: fetched-content-in-system-prompt
        return Agent(name="changelog", instructions=f"Summarize:\n{resp.text[:2000]}")

    def health(self, feed: str):
        resp = self.http.get(feed)
        # ok: fetched-content-in-system-prompt
        return Agent(name="changelog", instructions=f"The feed answered {resp.status_code}.")


class HandbookBot:
    def __init__(self, retriever, tavily_client):
        self.retriever = retriever
        self.tavily = tavily_client

    def answer(self, question: str):
        docs = self.retriever.invoke(question)
        context = "\n\n".join(d.page_content for d in docs)
        # ruleid: fetched-content-in-system-prompt
        return Agent(name="handbook", instructions=f"Answer from:\n{context}")

    def web_answer(self, question: str):
        found = self.tavily.search(question, max_results=3)
        # ruleid: fetched-content-in-system-prompt
        return Agent(name="web", instructions=f"Sources: {found['results']}")


def serp_wrapper_brief(topic: str):
    findings = SerpAPIWrapper().run(topic)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="brief", instructions=f"Background from the web:\n{findings}")


def serp_client_brief(topic: str):
    client = serpapi.Client(api_key="fake-serpapi-key")
    results = client.search({"engine": "google", "q": topic})
    snippets = "\n".join(r["snippet"] for r in results["organic_results"])
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="brief", instructions=f"Background from the web:\n{snippets}")


def legacy_serp_brief(topic: str):
    results = GoogleSearch({"q": topic, "api_key": "fake-serpapi-key"}).get_dict()
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="brief", instructions=f"Background: {results['organic_results']}")


def ddgs_brief(topic: str):
    hits = DDGS().text(topic, max_results=5)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="brief", instructions=f"Search results: {hits}")


def ddgs_with_brief(topic: str):
    with DDGS() as ddgs:
        hits = ddgs.news(topic, max_results=5)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="brief", instructions=f"News: {hits}")


def lc_search_tools_brief(topic: str):
    ddg = DuckDuckGoSearchRun().invoke(topic)
    brave = BraveSearch.from_api_key(api_key="fake-brave-key", search_kwargs={"count": 3}).run(topic)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="brief", instructions=f"DuckDuckGo: {ddg}\nBrave: {brave}")


def google_bing_brief(topic: str):
    google = GoogleSearchAPIWrapper().results(topic, 3)
    bing = BingSearchAPIWrapper().run(topic)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="brief", instructions=f"Google: {google}\nBing: {bing}")


def cse_brief(topic: str):
    service = build("customsearch", "v1", developerKey="fake-google-key")
    res = service.cse().list(q=topic, cx="fake-engine-id").execute()
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="brief", instructions=f"Results: {res['items']}")


def jina_reader_summary(url: str):
    page = requests.get(f"https://r.jina.ai/{url}", timeout=20)
    # ruleid: fetched-content-in-system-prompt
    return Agent(name="reader", instructions=f"Summarize this page:\n{page.text[:6000]}")


def search_settings(web_search_config: dict):
    # ok: fetched-content-in-system-prompt
    return Agent(name="brief", instructions=f"Search engine: {web_search_config['engine']}")


async def describe_by_script(url: str):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        body = await page.evaluate("() => document.body.innerText")
        lead = await page.eval_on_selector("article p", "e => e.textContent")
        rendered = await page.inner_text("main")
        depth = await page.evaluate("() => window.scrollY")
    # ruleid: fetched-content-in-system-prompt
    first = Agent(name="browse", instructions=f"Page text:\n{body}")
    # ruleid: fetched-content-in-system-prompt
    second = Agent(name="browse", instructions=f"Lead paragraph: {lead}")
    # ruleid: fetched-content-in-system-prompt
    third = Agent(name="browse", instructions=f"Rendered page:\n{rendered[:4000]}")
    # ok: fetched-content-in-system-prompt
    fourth = Agent(name="browse", instructions=f"The reader scrolled {depth} pixels.")
    return first, second, third, fourth


FAQ_SLOT = "faq_items"
faq_items_prompt = ChatPromptTemplate.from_messages(
    [
        # ruleid: fetched-content-in-system-prompt
        ("system", "Answer from these FAQ items:\n{faq_items}"),
        ("human", "{input}"),
    ]
)
faq_items_chain = create_stuff_documents_chain(llm, faq_items_prompt, document_variable_name=FAQ_SLOT)


def notes_chain():
    slot = "notes"
    notes_prompt = ChatPromptTemplate.from_messages(
        [
            # ok: fetched-content-in-system-prompt
            ("system", "Use the notes in the user message, and cite them."),
            ("human", "{notes}\n\n{input}"),
        ]
    )
    return create_stuff_documents_chain(llm, notes_prompt, document_variable_name=slot)

