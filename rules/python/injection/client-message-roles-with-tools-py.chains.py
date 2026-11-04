from fastapi import FastAPI, Request
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

app = FastAPI()
llm = ChatOpenAI(model="gpt-5")


@tool
def close_ticket(ticket_id: str) -> str:
    """Close a helpdesk ticket."""
    return f"closed {ticket_id}"


prompt = ChatPromptTemplate.from_messages(
    [("system", "You manage helpdesk tickets."), MessagesPlaceholder("history"), ("human", "{question}")]
)
agent_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You manage helpdesk tickets."),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

chain = prompt | llm.bind_tools([close_ticket])
model_with_tools = llm.bind_tools([close_ticket])
routed = prompt | model_with_tools
plain_chain = prompt | llm | StrOutputParser()
executor = AgentExecutor(
    agent=create_tool_calling_agent(llm, [close_ticket], agent_prompt), tools=[close_ticket]
)


@app.post("/tickets/chat")
async def ticket_chat(request: Request):
    body = await request.json()
    reply = await chain.ainvoke(
        # ruleid: client-message-roles-with-tools-py
        {"question": body["question"], "history": body["history"]}
    )
    # The tool-bound chain only proposes calls; they run here.
    for call in reply.tool_calls:
        await close_ticket.ainvoke(call)
    again = await routed.ainvoke(
        # ruleid: client-message-roles-with-tools-py
        {"question": body["question"], "history": body["history"]}
    )
    text = await plain_chain.ainvoke(
        # ok: client-message-roles-with-tools-py
        {"question": body["question"], "history": body["history"]}
    )
    ran = await executor.ainvoke(
        # ruleid: client-message-roles-with-tools-py
        {"input": body["question"], "chat_history": body.get("chat_history", [])}
    )
    trimmed = await chain.ainvoke(
        # ok: client-message-roles-with-tools-py
        {"question": body["question"], "history": [("human", str(t["content"])) for t in body["history"]]}
    )
    return {"reply": reply.content, "again": again.content, "text": text, "ran": ran, "trimmed": trimmed.content}
