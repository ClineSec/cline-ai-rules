"""Anomaly search: "has this metric dipped like this before?" over past anomaly write-ups.

Write-ups from every business unit sit in one Milvus collection, each row tagged with its
unit. The Anomalies page calls this blueprint; power users get an "advanced filter" box that
takes a Milvus expression, for things like `week >= "2026-W30" and severity > 2`.
"""

import os

from flask import Blueprint, abort, jsonify, request, session
from pymilvus import MilvusClient

bp = Blueprint("anomaly_search", __name__, url_prefix="/anomalies")

COLLECTION = "anomaly_writeups"
FIELDS = ["metric", "week", "severity", "summary"]


def _milvus() -> MilvusClient:
    return MilvusClient(uri=os.environ.get("MILVUS_URI", "http://milvus.internal.invalid:19530"))


def _unit() -> str:
    unit = session.get("unit")
    if not unit:
        abort(401)
    return unit


def _embed(text: str) -> list[float]:
    from insights.llm import embed

    return embed(text)


@bp.post("/similar")
def similar():
    payload = request.get_json(silent=True) or {}
    unit = _unit()
    # The page pre-fills the box with the reader's unit, so the default only covers
    # an empty box.
    expr = payload.get("expr", "").strip() or f'unit == "{unit}"'
    hits = _milvus().search(
        COLLECTION,
        data=[_embed(payload.get("q", ""))],
        limit=10,
        filter=expr,
        output_fields=FIELDS,
    )
    return jsonify(hits)


@bp.get("/by-metric")
def by_metric():
    unit = _unit()
    weeks = request.args.getlist("week")
    rows = _milvus().query(
        COLLECTION,
        filter="unit == {unit} and metric == {metric} and week in {weeks}",
        filter_params={"unit": unit, "metric": request.args.get("metric", ""), "weeks": weeks},
        output_fields=FIELDS,
        limit=50,
    )
    return jsonify(rows)
