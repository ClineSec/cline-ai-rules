# ADK's to_a2a() returns a Starlette app; security_schemes= only goes on the card.
import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent

root_agent = LlmAgent(name="weather", model="gemini-3-flash", instruction="Answer weather questions.")
a2a_app = to_a2a(root_agent, port=8001, security_schemes={"apiKey": {"type": "apiKey", "in": "header", "name": "X-Key"}})

# ruleid: a2a-server-without-auth
uvicorn.run(a2a_app, host="0.0.0.0", port=8001)
