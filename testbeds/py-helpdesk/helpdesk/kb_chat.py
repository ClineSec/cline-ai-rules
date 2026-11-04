"""Knowledge-base chat for the staff intranet: a LangGraph agent that searches the KB and can
file a ticket. The intranet widget posts the running transcript as JSON."""

from fastapi import APIRouter, Request
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

router = APIRouter(prefix="/kb", tags=["kb"])

KB_PROMPT = "Answer from the Example Corp IT knowledge base. Cite the article ID you used."


@tool
def search_kb(query: str) -> str:
    """Search knowledge-base articles and return the top three summaries."""
    return f"KB-1042: How to connect to the VPN (matched {query!r})"


@tool
def file_ticket(summary: str, requester_email: str) -> str:
    """File a service-desk ticket on behalf of the requester."""
    return f"filed ticket for {requester_email}: {summary[:80]}"


kb_agent = create_react_agent(ChatOpenAI(model="gpt-5-mini"), [search_kb, file_ticket], prompt=KB_PROMPT)


@router.post("/chat")
async def kb_chat(request: Request) -> dict:
    payload = await request.json()
    state = await kb_agent.ainvoke({"messages": payload["history"]})
    return {"reply": state["messages"][-1].content}


@router.post("/ask")
async def kb_ask(request: Request) -> dict:
    """Single questions from the intranet search box: one user turn, no history."""
    payload = await request.json()
    state = await kb_agent.ainvoke({"messages": [("user", str(payload["question"]))]})
    return {"reply": state["messages"][-1].content}
