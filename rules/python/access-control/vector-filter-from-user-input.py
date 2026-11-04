import json
from typing import Any

import chromadb
from chromadb import Search
from fastapi import Depends, FastAPI
from flask import Flask, g, request
from langchain_core.vectorstores import VectorStoreRetriever
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from pinecone import Pinecone
from pydantic import BaseModel
from qdrant_client import QdrantClient, models

api = FastAPI()
app = Flask(__name__)
chroma = chromadb.HttpClient(host="chroma.internal.invalid")
notes = chroma.get_collection("notes")
pc = Pinecone(api_key="pc-test-not-a-key")
index = pc.Index(host="kb-example.svc.example.invalid")
qdrant = QdrantClient(url="http://qdrant.internal.invalid:6333")

FILTER_PRESETS = {"recent": {"year": {"$gte": 2026}}, "all": {}}
FILTER_KEYS = {"topic", "locale"}


class SearchBody(BaseModel):
    query: str
    filters: dict[str, Any] = {}
    topic: str = ""


# ---- Chroma ---------------------------------------------------------------------------------

@app.post("/notes/search")
def chroma_whole_filter():
    payload = request.get_json()
    # ruleid: vector-filter-from-user-input
    return notes.query(query_texts=[payload["q"]], n_results=8, where=payload["filters"])


@app.get("/notes/find")
def chroma_query_string_filter():
    raw = request.args.get("filter", "{}")
    flt = json.loads(raw)
    # ruleid: vector-filter-from-user-input
    return notes.get(where=flt, limit=20)


@api.post("/notes/purge")
def chroma_delete(body: SearchBody):
    # ruleid: vector-filter-from-user-input
    notes.delete(where=body.filters)


@app.post("/notes/scoped")
def chroma_spread_last():
    extra = request.get_json().get("filters", {})
    # The request's keys come last, so {"workspace_id": "other-ws"} replaces the server's.
    # ruleid: vector-filter-from-user-input
    return notes.query(query_texts=["x"], where={"workspace_id": g.workspace_id, **extra})


@app.post("/notes/by-field")
def chroma_request_key():
    body = request.get_json()
    # ruleid: vector-filter-from-user-input
    return notes.query(query_texts=["x"], where={"workspace_id": g.workspace_id, body["field"]: body["value"]})


@app.post("/notes/search-api")
def chroma_search_api():
    body = request.get_json()
    # ruleid: vector-filter-from-user-input
    return notes.search(Search().where(body["where"]).limit(10))


@app.post("/notes/topic")
def chroma_field_value_ok():
    body = request.get_json()
    # ok: vector-filter-from-user-input
    return notes.query(query_texts=[body["q"]], where={"$and": [{"workspace_id": g.workspace_id}, {"topic": body["topic"]}]})


@app.post("/notes/topic2")
def chroma_variable_ok():
    body = request.get_json()
    flt = {"workspace_id": g.workspace_id, "topic": body["topic"]}
    # ok: vector-filter-from-user-input
    return notes.query(query_texts=[body["q"]], where=flt)


@app.post("/notes/text")
def chroma_where_document_ok():
    body = request.get_json()
    # where_document only matches document text, and is ANDed with the server's where.
    # ok: vector-filter-from-user-input
    return notes.query(query_texts=["x"], where={"workspace_id": g.workspace_id}, where_document=body["contains"])


@app.post("/notes/preset")
def chroma_preset_ok():
    preset = request.args.get("preset", "all")
    # ok: vector-filter-from-user-input
    return notes.query(query_texts=["x"], where=FILTER_PRESETS[preset])


def scoped_filter(workspace_id, extra):
    return {"$and": [{"workspace_id": workspace_id}, *[{k: v} for k, v in extra.items() if k in FILTER_KEYS]]}


@app.post("/notes/helper")
def chroma_helper_ok():
    body = request.get_json()
    # ok: vector-filter-from-user-input
    return notes.query(query_texts=["x"], where=scoped_filter(g.workspace_id, body["filters"]))


@app.post("/notes/allowed-keys")
def chroma_allowed_keys_ok():
    body = request.get_json()
    picked = {k: v for k, v in body["filters"].items() if k in FILTER_KEYS}
    # ok: vector-filter-from-user-input
    return notes.query(query_texts=["x"], where={"$and": [{"workspace_id": g.workspace_id}, picked]})


@app.post("/notes/server-last")
def chroma_server_key_last_ok():
    extra = request.get_json().get("filters", {})
    # ok: vector-filter-from-user-input
    return notes.query(query_texts=["x"], where={**extra, "workspace_id": g.workspace_id})


# ---- Pinecone -------------------------------------------------------------------------------

@api.post("/kb/search")
def pinecone_query(body: SearchBody):
    # ruleid: vector-filter-from-user-input
    return index.query(vector=[0.1] * 8, top_k=5, filter=body.filters, namespace="help-center")


@api.post("/kb/records")
def pinecone_search_records(body: SearchBody):
    return index.search(
        namespace="help-center",
        # ruleid: vector-filter-from-user-input
        query={"inputs": {"text": body.query}, "top_k": 5, "filter": body.filters},
    )


@api.post("/kb/tenant")
def pinecone_per_tenant_namespace_ok(body: SearchBody, user=Depends(lambda: None)):
    # The namespace is the caller's own, so the filter only narrows inside it.
    # ok: vector-filter-from-user-input
    return index.query(vector=[0.1] * 8, top_k=5, filter=body.filters, namespace=f"org-{user.org_id}")


@api.post("/kb/scoped")
def pinecone_field_value_ok(body: SearchBody, user=Depends(lambda: None)):
    # ok: vector-filter-from-user-input
    return index.query(vector=[0.1] * 8, top_k=5, filter={"org_id": user.org_id, "topic": body.topic})


@api.post("/kb/purge")
def pinecone_delete(body: SearchBody):
    # ruleid: vector-filter-from-user-input
    index.delete(filter=body.filters, namespace="help-center")


# ---- Qdrant ---------------------------------------------------------------------------------

@api.post("/docs/search")
def qdrant_query_points(body: SearchBody):
    return qdrant.query_points(
        collection_name="docs",
        query=[0.1] * 8,
        # ruleid: vector-filter-from-user-input
        query_filter=models.Filter.model_validate(body.filters),
        limit=5,
    )


@api.post("/docs/scroll")
def qdrant_scroll(body: SearchBody):
    # ruleid: vector-filter-from-user-input
    return qdrant.scroll("docs", scroll_filter=models.Filter(**body.filters), limit=50)


@api.post("/docs/purge")
def qdrant_delete(body: SearchBody):
    # ruleid: vector-filter-from-user-input
    qdrant.delete("docs", points_selector=models.FilterSelector(filter=body.filters))


@api.post("/docs/topic")
def qdrant_builder_ok(body: SearchBody, user=Depends(lambda: None)):
    return qdrant.query_points(
        collection_name="docs",
        query=[0.1] * 8,
        # ok: vector-filter-from-user-input
        query_filter=models.Filter(must=[
            models.FieldCondition(key="org_id", match=models.MatchValue(value=user.org_id)),
            models.FieldCondition(key="topic", match=models.MatchValue(value=body.topic)),
        ]),
    )


@api.post("/docs/sharded")
def qdrant_shard_key_ok(body: SearchBody, user=Depends(lambda: None)):
    # ok: vector-filter-from-user-input
    return qdrant.count("docs", count_filter=body.filters, shard_key_selector=user.org_id)


# ---- LangChain ------------------------------------------------------------------------------

@api.post("/playbooks/search")
def langchain_similarity(body: SearchBody, store=Depends(lambda: None)):
    # ruleid: vector-filter-from-user-input
    return store.similarity_search(body.query, k=4, filter=body.filters)


@api.post("/playbooks/retriever")
def langchain_retriever(body: SearchBody, store=Depends(lambda: None)):
    # ruleid: vector-filter-from-user-input
    retriever = store.as_retriever(search_kwargs={"k": 6, "filter": body.filters})
    return retriever.invoke(body.query)


@api.post("/playbooks/retriever2")
def langchain_retriever_kwargs(body: SearchBody, retriever=Depends(lambda: None)):
    # ruleid: vector-filter-from-user-input
    retriever.search_kwargs["filter"] = body.filters
    return retriever.invoke(body.query)


@api.post("/playbooks/retriever3")
def langchain_invoke_kwargs(body: SearchBody, retriever=Depends(lambda: None)):
    # ruleid: vector-filter-from-user-input
    return retriever.invoke(body.query, filter=body.filters)


@api.post("/playbooks/retriever4")
def langchain_retriever_ok(body: SearchBody, store=Depends(lambda: None), user=Depends(lambda: None)):
    # ok: vector-filter-from-user-input
    retriever = VectorStoreRetriever(vectorstore=store, search_kwargs={"k": 6, "filter": {"org_id": user.org_id, "topic": body.topic}})
    return retriever.invoke(body.query)


# ---- LlamaIndex -----------------------------------------------------------------------------

@api.post("/wiki/ask")
def llamaindex_filters(body: SearchBody, wiki=Depends(lambda: None)):
    filters = MetadataFilters.from_dict(body.filters)
    # ruleid: vector-filter-from-user-input
    engine = wiki.as_query_engine(similarity_top_k=4, filters=filters)
    return str(engine.query(body.query))


@api.post("/wiki/ask-scoped")
def llamaindex_filters_ok(body: SearchBody, wiki=Depends(lambda: None), user=Depends(lambda: None)):
    filters = MetadataFilters(filters=[
        MetadataFilter(key="org_id", value=user.org_id),
        MetadataFilter(key="topic", value=body.topic),
    ])
    # ok: vector-filter-from-user-input
    engine = wiki.as_query_engine(similarity_top_k=4, filters=filters)
    return str(engine.query(body.query))


# ---- More request shapes --------------------------------------------------------------------

def django_search(request):
    params = json.loads(request.body)
    # ruleid: vector-filter-from-user-input
    return notes.query(query_texts=[params["q"]], where=params["where"])


@api.post("/async/search")
async def starlette_async(request: Any, store=Depends(lambda: None)):
    data = await request.json()
    # ruleid: vector-filter-from-user-input
    return await store.amax_marginal_relevance_search(data["q"], k=4, filter=data.get("filter"))


@api.post("/kb/all-namespaces")
def pinecone_query_namespaces(filters: dict[str, Any], q: str):
    # ruleid: vector-filter-from-user-input
    return index.query_namespaces(vector=[0.1] * 8, namespaces=["en", "de"], metric="cosine", filter=filters)


@api.post("/notes/search-init")
def chroma_search_init(body: SearchBody):
    # ruleid: vector-filter-from-user-input
    return notes.search(Search(where=body.filters))


@api.post("/playbooks/kwargs")
def langchain_whole_search_kwargs(body: SearchBody, store=Depends(lambda: None)):
    # ruleid: vector-filter-from-user-input
    return store.as_retriever(search_kwargs=body.filters).invoke(body.query)


@api.post("/kb/merge-bad")
def merge_request_last(body: SearchBody, user=Depends(lambda: None)):
    # ruleid: vector-filter-from-user-input
    return index.query(vector=[0.1] * 8, top_k=5, filter={"org_id": user.org_id} | body.filters)


@api.post("/kb/merge-ok")
def merge_server_last(body: SearchBody, user=Depends(lambda: None)):
    # ok: vector-filter-from-user-input
    return index.query(vector=[0.1] * 8, top_k=5, filter=body.filters | {"org_id": user.org_id})


@api.post("/docs/merge-ok")
def qdrant_spread_with_server_keys(body: SearchBody, user=Depends(lambda: None)):
    tenant = models.FieldCondition(key="org_id", match=models.MatchValue(value=user.org_id))
    # A duplicate `must` raises instead of replacing the server's condition.
    # ok: vector-filter-from-user-input
    return qdrant.query_points("docs", query=[0.1] * 8, query_filter=models.Filter(must=[tenant], **body.filters))


@api.post("/notes/saved")
def saved_view_ok(view_id: str, saved_views=Depends(lambda: {})):
    # ok: vector-filter-from-user-input
    return notes.query(query_texts=["x"], where=saved_views.get(view_id))


@app.post("/kb/extra")
def spread_of_call_last():
    body = request.get_json()
    # ruleid: vector-filter-from-user-input
    return index.query(vector=[0.1] * 8, top_k=5, filter={"org_id": g.org_id, **body.get("filters", {})})


@api.post("/kb/retag")
def pinecone_update_by_filter(body: SearchBody):
    # ruleid: vector-filter-from-user-input
    index.update(filter=body.filters, set_metadata={"reviewed": True}, namespace="help-center")
    params = {"top_k": 5}
    # A dict's own update() just stores a key.
    # ok: vector-filter-from-user-input
    params.update(filter=body.filters)
    return params


@api.post("/docs/facets")
def qdrant_facet(body: SearchBody):
    # ruleid: vector-filter-from-user-input
    return qdrant.facet("docs", key="topic", facet_filter=body.filters)


@api.post("/wiki/retriever")
def llamaindex_retriever(body: SearchBody, wiki=Depends(lambda: None)):
    from llama_index.core.retrievers import VectorIndexRetriever
    # ruleid: vector-filter-from-user-input
    retriever = VectorIndexRetriever(index=wiki, similarity_top_k=4, filters=MetadataFilters.from_dicts(body.filters["items"]))
    return retriever.retrieve(body.query)


# ---- Milvus ---------------------------------------------------------------------------------

from pymilvus import AnnSearchRequest, MilvusClient, WeightedRanker

milvus = MilvusClient(uri="http://milvus.internal.invalid:19530")


class MilvusBody(BaseModel):
    vector: list[float]
    filter: str = ""
    topic: str = ""


@api.post("/tickets/search")
def milvus_whole_expression(body: MilvusBody):
    # ruleid: vector-filter-from-user-input
    return milvus.search("tickets", data=[body.vector], limit=5, filter=body.filter)


@app.post("/tickets/query")
def milvus_query_and_delete():
    expr = request.args.get("filter", "").strip()
    # ruleid: vector-filter-from-user-input
    rows = milvus.query("tickets", filter=expr, output_fields=["id", "title"])
    # ruleid: vector-filter-from-user-input
    milvus.delete("tickets", filter=request.json["filter"])
    return rows


@api.post("/tickets/hybrid")
def milvus_hybrid(body: MilvusBody):
    # ruleid: vector-filter-from-user-input
    dense = AnnSearchRequest([body.vector], "dense", {"metric_type": "COSINE"}, limit=10, expr=body.filter)
    return milvus.hybrid_search("tickets", [dense], WeightedRanker(1.0), limit=5)


@api.post("/tickets/by-topic")
def milvus_server_expression(body: MilvusBody, user=Depends(lambda: None)):
    # Request text pasted into the expression can close the quote and add `or ...`.
    # ruleid: vector-filter-from-user-input
    milvus.search("tickets", data=[body.vector], filter=f'org_id == "{user.org_id}" and topic == "{body.topic}"')
    # ruleid: vector-filter-from-user-input
    milvus.query("tickets", filter='org_id == "{}" and topic == "{}"'.format(user.org_id, body.topic))
    # ruleid: vector-filter-from-user-input
    milvus.query("tickets", filter=" and ".join([f'org_id == "{user.org_id}"', f'topic == "{body.topic}"']))
    # The server's expression with the request's value bound as a template parameter.
    # ok: vector-filter-from-user-input
    milvus.search("tickets", data=[body.vector], filter="org_id == {org} and topic == {topic}",
                  filter_params={"org": user.org_id, "topic": body.topic})
    # A quoted value can't leave its string.
    # ok: vector-filter-from-user-input
    milvus.query("tickets", filter=f"org_id == {json.dumps(user.org_id)} and topic == {json.dumps(body.topic)}")
    # ok: vector-filter-from-user-input
    return milvus.query("tickets", filter=f'org_id == "{user.org_id}"', output_fields=[body.topic])


# ---- MongoDB Atlas Vector Search ------------------------------------------------------------

from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient

articles = MongoClient("mongodb://mongo.internal.invalid")["kb"]["articles"]
atlas_store = MongoDBAtlasVectorSearch(collection=articles, embedding=None, index_name="vector_index")


@api.post("/articles/search")
def atlas_aggregate(body: SearchBody, user=Depends(lambda: None)):
    # ruleid: vector-filter-from-user-input
    hits = articles.aggregate([{"$vectorSearch": {"index": "vector_index", "path": "embedding", "queryVector": [0.1] * 8, "numCandidates": 100, "limit": 5, "filter": body.filters}}])
    pipeline = [
        # ok: vector-filter-from-user-input
        {"$vectorSearch": {"index": "vector_index", "path": "embedding", "queryVector": [0.1] * 8, "numCandidates": 100, "limit": 5, "filter": {"org_id": user.org_id, "topic": body.topic}}},
        # A $match after the stage only narrows what it returned.
        # ok: vector-filter-from-user-input
        {"$match": body.filters},
    ]
    return list(hits) + list(articles.aggregate(pipeline))


@api.post("/articles/search/staged")
def atlas_pipeline_variable(body: SearchBody):
    pipeline = [
        # ruleid: vector-filter-from-user-input
        {"$vectorSearch": {"index": "vector_index", "path": "embedding", "queryVector": [0.1] * 8, "limit": 5, "filter": {"$or": body.filters["any"]} | body.filters}},
        {"$project": {"title": 1}},
    ]
    return list(articles.aggregate(pipeline))


@api.post("/articles/ask")
def atlas_langchain(body: SearchBody, user=Depends(lambda: None)):
    # ruleid: vector-filter-from-user-input
    docs = atlas_store.similarity_search(body.query, k=4, pre_filter=body.filters)
    # ruleid: vector-filter-from-user-input
    retriever = atlas_store.as_retriever(search_kwargs={"k": 4, "pre_filter": body.filters})
    # ok: vector-filter-from-user-input
    scoped = atlas_store.similarity_search(body.query, k=4, pre_filter={"org_id": {"$eq": user.org_id}, "topic": body.topic})
    return docs + scoped + retriever.invoke(body.query)
