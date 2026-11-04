""""Similar weeks": search past weekly reports, embedded into Pinecone after each send.

The index is shared by every business unit; each report carries its unit in the metadata.
"""

import json

from flask import Blueprint, jsonify, request, session
from flask.views import MethodView
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

bp = Blueprint("reports", __name__, url_prefix="/reports")

REPORTS = PineconeVectorStore(
    index_name="weekly-reports",
    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
)


class SimilarWeeks(MethodView):
    """POST {"question": ..., "filters": {...}} from the report sidebar."""

    def post(self):
        body = request.get_json(force=True)
        retriever = REPORTS.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 20, "filter": {"unit": session["unit"], **body.get("filters", {})}},
        )
        docs = retriever.invoke(body["question"])
        return jsonify([{"week": d.metadata["week"], "excerpt": d.page_content[:280]} for d in docs])


bp.add_url_rule("/similar", view_func=SimilarWeeks.as_view("similar"))


@bp.get("/similar/<week>")
def similar_to_week(week: str):
    extra = json.loads(request.args.get("filters", "{}"))
    docs = REPORTS.similarity_search(
        f"weekly growth report, week {week}",
        k=4,
        filter={**extra, "unit": session["unit"]},
    )
    return jsonify([d.metadata for d in docs])


@bp.post("/archive/search")
def archive_search():
    # Archived reports are kept in one namespace per unit.
    body = request.get_json(force=True)
    docs = REPORTS.similarity_search(body["question"], k=4, filter=body.get("filters"), namespace=f"archive-{session['unit']}")
    return jsonify([d.metadata for d in docs])
