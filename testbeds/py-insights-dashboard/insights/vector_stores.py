"""Vector store connections for the semantic search pages.

Metric notes and experiment write-ups live in the data platform's Qdrant cluster; dashboard
snapshots are embedded into Weaviate so the assistant can find "a chart like this one".
Connections are cached per process because Streamlit reruns the page script on every click.
"""

import os
from functools import lru_cache

import weaviate
from qdrant_client import QdrantClient
from weaviate.classes.init import AdditionalConfig, Auth, Timeout

# The data platform team runs this cluster; see the platform runbook for its network rules.
METRIC_NOTES_URL = "https://vectors.example.com:6333"
METRIC_NOTES_COLLECTION = "metric_notes"
EXPERIMENTS_COLLECTION = "experiment_writeups"

SNAPSHOT_HOST = "weaviate.example.com"
SNAPSHOT_GRPC_HOST = "weaviate-grpc.example.com"


@lru_cache(maxsize=1)
def metric_notes_store() -> QdrantClient:
    return QdrantClient(url=METRIC_NOTES_URL, timeout=20, prefer_grpc=False)


@lru_cache(maxsize=1)
def experiment_store() -> QdrantClient:
    # Experiments hold unreleased product numbers, so this collection's cluster key is required.
    return QdrantClient(url=METRIC_NOTES_URL, api_key=os.environ["QDRANT_API_KEY"], timeout=20)


def snapshot_store() -> weaviate.WeaviateClient:
    if os.environ.get("INSIGHTS_ENV") == "dev":
        return weaviate.connect_to_local()
    return weaviate.connect_to_custom(
        http_host=SNAPSHOT_HOST,
        http_port=443,
        http_secure=True,
        grpc_host=SNAPSHOT_GRPC_HOST,
        grpc_port=443,
        grpc_secure=True,
        headers={"X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"]},
        additional_config=AdditionalConfig(timeout=Timeout(init=10, query=30)),
    )


def partner_snapshot_store() -> weaviate.WeaviateClient:
    # The partner workspace is shared with an agency, so it uses its own key.
    return weaviate.connect_to_custom(
        http_host=SNAPSHOT_HOST,
        http_port=443,
        http_secure=True,
        grpc_host=SNAPSHOT_GRPC_HOST,
        grpc_port=443,
        grpc_secure=True,
        auth_credentials=Auth.api_key(os.environ["WEAVIATE_PARTNER_KEY"]),
    )


def similar_notes(vector: list[float], limit: int = 5) -> list[str]:
    hits = metric_notes_store().query_points(METRIC_NOTES_COLLECTION, query=vector, limit=limit)
    return [str(point.payload.get("title", "")) for point in hits.points]
