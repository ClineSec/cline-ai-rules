# Not an A2A server: a FastAPI app that only calls A2A agents as a client.
import uvicorn
from a2a.client import ClientFactory
from fastapi import FastAPI

app = FastAPI()
factory = ClientFactory()

# ok: a2a-server-without-auth
uvicorn.run(app, host="0.0.0.0", port=8000)
