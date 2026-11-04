"""Live chat for the self-service portal, over a WebSocket."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

router = APIRouter()

PORTAL_SYSTEM = "You are the Example Cloud self-service assistant, talking to {display_name}. Answer questions about accounts, VPN, and printers; hand anything else to a human."
portal_prompt = ChatPromptTemplate.from_messages(
    [("system", PORTAL_SYSTEM), MessagesPlaceholder("history"), ("human", "{question}")]
)
portal_chain = portal_prompt | ChatOpenAI(model="gpt-5-mini")


@router.websocket("/portal/chat")
async def portal_chat(websocket: WebSocket):
    await websocket.accept()
    # The portal's first frame says who is signed in, so the assistant can greet them.
    hello = await websocket.receive_json()
    history = []
    try:
        while True:
            question = await websocket.receive_text()
            reply = await portal_chain.ainvoke(
                {
                    "display_name": hello.get("display_name", "a customer"),
                    "history": history,
                    "question": question,
                }
            )
            history += [HumanMessage(question), AIMessage(reply.content)]
            await websocket.send_text(reply.content)
    except WebSocketDisconnect:
        return
