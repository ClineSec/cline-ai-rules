import uvicorn
from fasta2a.pydantic_ai import agent_to_a2a
from pydantic_ai import Agent

agent = Agent("openai:gpt-5.5", instructions="Summarize support tickets.")
app = agent_to_a2a(agent, name="ticket-summarizer", url="https://tickets.example.com")


def run() -> None:
    # ruleid: a2a-server-without-auth
    uvicorn.run(app, host="0.0.0.0", port=8000)
