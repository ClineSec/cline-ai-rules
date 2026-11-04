"""Playbooks: "what did we do last time conversion dropped?" over response playbooks.

Playbooks live in a MongoDB Atlas collection with a vector index; each unit writes its own,
and some are marked shared. The chat side panel searches them for the reader's unit.
"""

import os

from flask import Blueprint, abort, jsonify, request, session
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient

bp = Blueprint("playbooks", __name__, url_prefix="/playbooks")

_client = MongoClient(os.environ.get("MONGODB_URI", "mongodb://mongo.internal.invalid"))
playbooks = _client["insights"]["playbooks"]


def _unit() -> str:
    unit = session.get("unit")
    if not unit:
        abort(401)
    return unit


def _embed(text: str) -> list[float]:
    from insights.llm import embed

    return embed(text)


@bp.post("/search")
def search():
    payload = request.get_json(silent=True) or {}
    unit = _unit()
    stage = {
        "$vectorSearch": {
            "index": "playbook_vectors",
            "path": "embedding",
            "queryVector": _embed(payload.get("q", "")),
            "numCandidates": 200,
            "limit": 6,
            # The side panel sends {"unit": ...} plus any tag chips the reader picked.
            "filter": payload.get("filter") or {"unit": unit},
        }
    }
    found = playbooks.aggregate([stage, {"$project": {"embedding": 0}}])
    return jsonify([{**doc, "_id": str(doc["_id"])} for doc in found])


@bp.post("/suggest")
def suggest():
    payload = request.get_json(silent=True) or {}
    store = MongoDBAtlasVectorSearch(
        collection=playbooks,
        embedding=None,
        index_name="playbook_vectors",
        text_key="body",
    )
    tags = [str(t) for t in payload.get("tags", [])][:5]
    docs = store.similarity_search(
        payload.get("q", ""),
        k=4,
        pre_filter={"$or": [{"unit": {"$eq": _unit()}}, {"shared": True}], "tags": {"$in": tags}},
    )
    return jsonify([d.page_content for d in docs])
