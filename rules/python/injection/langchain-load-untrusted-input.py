import json

from fastapi import FastAPI, Request, WebSocket
from flask import Flask, request
from langchain_core.load import load, loads
from langchain_core.load.load import Reviver
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

app = Flask(__name__)
api = FastAPI()

SAVED_PROMPTS = {"weekly": '{"lc": 1, "type": "constructor", "id": ["langchain_core", "prompts"]}'}


class PromptImport(BaseModel):
    name: str
    manifest: dict


@app.post("/prompts/import")
def import_prompt():
    # ruleid: langchain-load-untrusted-input
    prompt = loads(request.get_data(as_text=True))
    return {"variables": prompt.input_variables}


@app.post("/prompts/import-json")
def import_prompt_json():
    payload = request.get_json()
    # ruleid: langchain-load-untrusted-input
    prompt = load(payload["prompt"], allowed_objects="core")
    return {"variables": prompt.input_variables}


@api.post("/chains/import")
async def import_chain(body: PromptImport):
    # ruleid: langchain-load-untrusted-input
    chain = load(body.manifest, allowed_objects=[ChatPromptTemplate, ChatOpenAI])
    return {"name": body.name, "steps": len(chain.steps)}


@api.post("/chains/import-raw")
async def import_chain_raw(req: Request):
    raw = await req.body()
    # ruleid: langchain-load-untrusted-input
    chain = json.loads(raw, object_hook=Reviver())
    return {"kind": type(chain).__name__}


@api.websocket("/chains/live")
async def live_chain(websocket: WebSocket):
    text = await websocket.receive_text()
    # ruleid: langchain-load-untrusted-input
    chain = loads(text=text)
    await websocket.send_text(type(chain).__name__)


# --- near misses --------------------------------------------------------------------------


@app.post("/history/import")
def import_history():
    # ok: langchain-load-untrusted-input
    messages = loads(request.get_data(as_text=True), allowed_objects="messages")
    return {"count": len(messages)}


@app.post("/history/import-listed")
def import_history_listed():
    # ok: langchain-load-untrusted-input
    messages = load(request.get_json(), allowed_objects=[AIMessage, HumanMessage])
    return {"count": len(messages)}


@app.post("/prompts/run")
def run_saved_prompt():
    name = request.args["name"]
    # ok: langchain-load-untrusted-input
    prompt = loads(SAVED_PROMPTS[name])
    return {"variables": prompt.input_variables}


@app.post("/prompts/restore")
def restore_all_partners():
    # Reported by langchain-load-unsafe-objects instead.
    # ok: langchain-load-untrusted-input
    prompt = loads(request.get_data(as_text=True), allowed_objects="all")
    return {"variables": prompt.input_variables}


@app.post("/prompts/preview")
def preview_prompt():
    # ok: langchain-load-untrusted-input
    data = json.loads(request.get_data(as_text=True))
    return {"keys": sorted(data)}
