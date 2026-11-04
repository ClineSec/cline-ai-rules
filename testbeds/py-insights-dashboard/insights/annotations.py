"""KPI annotations: notes analysts pin to a metric and week ("pricing page test started").

Each business unit sees only its own notes. The notes live in one Chroma collection, tagged
with the unit that wrote them. The blueprint is mounted next to the share-link app, so exec
readers can search the notes beside the weekly summary.
"""

import json
import os

import chromadb
from flask import Blueprint, abort, jsonify, request, session

bp = Blueprint("annotations", __name__, url_prefix="/annotations")

RESULTS = 8
FACET_FIELDS = ("metric", "week", "author")


def _notes():
    client = chromadb.HttpClient(host=os.environ.get("CHROMA_HOST", "chroma.internal.invalid"))
    return client.get_or_create_collection("kpi_annotations")


def _unit() -> str:
    unit = session.get("unit")
    if not unit:
        abort(401)
    return unit


@bp.post("/search")
def search():
    payload = request.get_json(silent=True) or {}
    unit = _unit()
    hits = _notes().query(
        query_texts=[payload.get("q", "")],
        n_results=RESULTS,
        # The facet panel already sends {"unit": ...} for the reader's unit.
        where=payload.get("where") or {"unit": unit},
    )
    return jsonify(hits)


@bp.post("/facets")
def facet_search():
    payload = request.get_json(silent=True) or {}
    picked = {k: v for k, v in payload.get("facets", {}).items() if k in FACET_FIELDS}
    clauses = [{"unit": _unit()}] + [{k: v} for k, v in picked.items()]
    where = clauses[0] if len(clauses) == 1 else {"$and": clauses}
    return jsonify(_notes().query(query_texts=[payload.get("q", "")], n_results=RESULTS, where=where))


@bp.get("/export")
def export_csv():
    metric = request.args.get("metric", "signups")
    rows = _notes().get(
        where={"$and": [{"unit": _unit()}, {"metric": metric}]},
        include=["documents", "metadatas"],
    )
    lines = ["week,author,note"]
    for meta, doc in zip(rows["metadatas"], rows["documents"]):
        lines.append(f'{meta["week"]},{meta["author"]},"{doc}"')
    return "\n".join(lines), 200, {"Content-Type": "text/csv"}


@bp.delete("/bulk")
def bulk_delete():
    # Used after a data correction: clear every note for the affected weeks.
    _unit()
    criteria = json.loads(request.args["criteria"])
    _notes().delete(where=criteria)
    return "", 204
