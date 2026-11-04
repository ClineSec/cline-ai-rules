# pydantic-ai 1.x: Agent.to_a2a() (removed in 2.x; fasta2a's agent_to_a2a replaced it).
import uvicorn
from pydantic_ai import Agent

agent = Agent("openai:gpt-5", instructions="Summarize support tickets.")
app = agent.to_a2a()
# ruleid: a2a-server-without-auth
uvicorn.run(app, host="0.0.0.0", port=8000)
