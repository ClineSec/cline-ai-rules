import os

import chromadb
import weaviate
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_community.vectorstores.milvus import Milvus as LegacyMilvus
from langchain_milvus import Milvus
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.vector_stores.milvus import MilvusVectorStore
from pymilvus import AsyncMilvusClient, MilvusClient, connections
from qdrant_client import AsyncQdrantClient, QdrantClient
from weaviate.classes.init import Auth
from weaviate.connect import ConnectionParams

SEARCH_URL = "https://vectors.example.com:6333"
LOCAL_URL = "http://localhost:6333"


def chroma_clients():
    # ruleid: vector-db-client-without-auth
    a = chromadb.HttpClient(host="chroma.example.com", port=8000, ssl=True)
    # ruleid: vector-db-client-without-auth
    b = chromadb.HttpClient("203.0.113.10", 8000)
    # ruleid: vector-db-client-without-auth
    c = chromadb.HttpClient(host="chroma.example.com", settings=Settings(anonymized_telemetry=False))
    # ruleid: vector-db-client-without-auth
    d = chromadb.Client(Settings(chroma_api_impl="rest", chroma_server_host="chroma.example.com"))
    # ok: vector-db-client-without-auth
    e = chromadb.HttpClient(host="chroma.example.com", headers={"X-Chroma-Token": os.environ["CHROMA_TOKEN"]})
    # ok: vector-db-client-without-auth
    f = chromadb.HttpClient(
        host="chroma.example.com",
        settings=Settings(
            chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
            chroma_client_auth_credentials=os.environ["CHROMA_TOKEN"],
        ),
    )
    # ok: vector-db-client-without-auth
    g = chromadb.HttpClient(host="localhost", port=8000)
    # ok: vector-db-client-without-auth
    h = chromadb.HttpClient(host="chroma", port=8000)
    # ok: vector-db-client-without-auth
    i = chromadb.HttpClient(host=os.environ["CHROMA_HOST"])
    # ok: vector-db-client-without-auth
    j = chromadb.PersistentClient(path="./chroma-data")
    # ok: vector-db-client-without-auth
    k = chromadb.CloudClient(tenant="analytics", database="prod")
    shared = Settings(chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider")
    # ok: vector-db-client-without-auth
    m = chromadb.HttpClient(host="chroma.example.com", settings=shared)
    return a, b, c, d, e, f, g, h, i, j, k, m


async def chroma_async():
    # ruleid: vector-db-client-without-auth
    return await chromadb.AsyncHttpClient(host="https://chroma.example.com")


def qdrant_clients():
    # ruleid: vector-db-client-without-auth
    a = QdrantClient(url="https://qdrant.example.com:6333")
    # ruleid: vector-db-client-without-auth
    b = QdrantClient(SEARCH_URL, timeout=30)
    # ruleid: vector-db-client-without-auth
    c = QdrantClient(host="203.0.113.20", port=6333, prefer_grpc=True)
    # ruleid: vector-db-client-without-auth
    d = AsyncQdrantClient(url="https://qdrant.example.com")
    # A host from the environment can't be judged, even with a remote default.
    # ok: vector-db-client-without-auth
    d2 = AsyncQdrantClient(url=os.getenv("QDRANT_URL", "https://qdrant.example.com"))
    # ok: vector-db-client-without-auth
    e = QdrantClient(url="https://qdrant.example.com:6333", api_key=os.environ["QDRANT_API_KEY"])
    # ok: vector-db-client-without-auth
    f = QdrantClient(url=SEARCH_URL, auth_token_provider=lambda: os.environ["QDRANT_JWT"])
    # ok: vector-db-client-without-auth
    g = QdrantClient(url=LOCAL_URL)
    # ok: vector-db-client-without-auth
    h = QdrantClient(":memory:")
    # ok: vector-db-client-without-auth
    i = QdrantClient(path="/var/lib/insights/qdrant")
    # ok: vector-db-client-without-auth
    j = QdrantClient(url="http://qdrant.vectors.svc.cluster.local:6333")
    # ok: vector-db-client-without-auth
    k = QdrantClient(url="https://3f1c.eu-central-1-0.aws.cloud.qdrant.io:6333", api_key=os.environ["QDRANT_API_KEY"])
    # ok: vector-db-client-without-auth
    m = QdrantClient(url="http://10.20.0.15:6333")
    opts = {"url": SEARCH_URL, "api_key": os.environ["QDRANT_API_KEY"]}
    # ok: vector-db-client-without-auth
    n = QdrantClient(**opts)
    return a, b, c, d, d2, e, f, g, h, i, j, k, m, n


def weaviate_clients():
    # ruleid: vector-db-client-without-auth
    a = weaviate.connect_to_custom(
        http_host="weaviate.example.com",
        http_port=443,
        http_secure=True,
        grpc_host="grpc.weaviate.example.com",
        grpc_port=443,
        grpc_secure=True,
        headers={"X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"]},
    )
    # ruleid: vector-db-client-without-auth
    b = weaviate.connect_to_local(host="203.0.113.30")
    # ruleid: vector-db-client-without-auth
    c = weaviate.WeaviateClient(connection_params=ConnectionParams.from_url("http://weaviate.example.com:8080", 50051))
    # ruleid: vector-db-client-without-auth
    d = weaviate.Client("http://weaviate.example.com:8080")
    # ok: vector-db-client-without-auth
    e = weaviate.connect_to_custom(
        http_host="weaviate.example.com",
        http_port=443,
        http_secure=True,
        grpc_host="grpc.weaviate.example.com",
        grpc_port=443,
        grpc_secure=True,
        auth_credentials=Auth.api_key(os.environ["WEAVIATE_API_KEY"]),
    )
    # ok: vector-db-client-without-auth
    f = weaviate.connect_to_local()
    # ok: vector-db-client-without-auth
    g = weaviate.connect_to_local(host="weaviate")
    # ok: vector-db-client-without-auth
    h = weaviate.connect_to_weaviate_cloud("abc.c0.europe-west3.gcp.weaviate.cloud", Auth.api_key(os.environ["WEAVIATE_API_KEY"]))
    # ok: vector-db-client-without-auth
    i = weaviate.connect_to_local(host="weaviate.example.com", headers={"Authorization": f"Bearer {os.environ['WEAVIATE_TOKEN']}"})
    return a, b, c, d, e, f, g, h, i


async def weaviate_async():
    # ruleid: vector-db-client-without-auth
    async with weaviate.use_async_with_local(host="weaviate.example.com") as client:
        return await client.is_ready()


def milvus_clients():
    # ruleid: vector-db-client-without-auth
    a = MilvusClient(uri="http://milvus.example.com:19530")
    # ruleid: vector-db-client-without-auth
    b = AsyncMilvusClient("https://203.0.113.40:19530", db_name="insights")
    # ruleid: vector-db-client-without-auth
    connections.connect("default", host="milvus.example.com", port="19530")
    # ok: vector-db-client-without-auth
    c = MilvusClient(uri="http://milvus.example.com:19530", token=os.environ["MILVUS_TOKEN"])
    # ok: vector-db-client-without-auth
    d = MilvusClient(uri="https://milvus.example.com:19530", user="insights", password=os.environ["MILVUS_PASSWORD"])
    # ok: vector-db-client-without-auth
    e = MilvusClient("./milvus_demo.db")
    # ok: vector-db-client-without-auth
    f = MilvusClient()
    # ok: vector-db-client-without-auth
    g = MilvusClient(uri="https://in03-1a2b.serverless.gcp-us-west1.cloud.zilliz.com", token=os.environ["ZILLIZ_TOKEN"])
    # ok: vector-db-client-without-auth
    connections.connect("default", host="milvus-standalone", port="19530")
    return a, b, c, d, e, f, g


def framework_stores(embeddings):
    # ruleid: vector-db-client-without-auth
    a = Chroma(collection_name="notes", embedding_function=embeddings, host="chroma.example.com", port=443, ssl=True)
    # ruleid: vector-db-client-without-auth
    b = Chroma.from_texts(["a note"], embeddings, host="203.0.113.41")
    # ruleid: vector-db-client-without-auth
    c = ChromaVectorStore(host="chroma.example.com", port="8000", collection_name="notes")
    # ruleid: vector-db-client-without-auth
    d = Milvus(embeddings, connection_args={"uri": "http://milvus.example.com:19530"})
    # ruleid: vector-db-client-without-auth
    e = Milvus.from_texts(["a note"], embeddings, connection_args={"uri": "http://203.0.113.42:19530", "db_name": "notes"})
    # ruleid: vector-db-client-without-auth
    f = LegacyMilvus(embeddings, connection_args={"host": "milvus.example.com", "port": "19530"})
    # ruleid: vector-db-client-without-auth
    g = MilvusVectorStore(uri="http://milvus.example.com:19530", dim=1536)
    # ok: vector-db-client-without-auth
    h = Chroma(collection_name="notes", embedding_function=embeddings, host="chroma.example.com", headers={"Authorization": f"Bearer {os.environ['CHROMA_TOKEN']}"})
    # ok: vector-db-client-without-auth
    i = Chroma(collection_name="notes", embedding_function=embeddings, persist_directory="./chroma")
    # ok: vector-db-client-without-auth
    j = Chroma(host="chroma.example.com", client_settings=Settings(chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider", chroma_client_auth_credentials=os.environ["CHROMA_TOKEN"]))
    # ok: vector-db-client-without-auth
    k = ChromaVectorStore(host="chroma.example.com", port="8000", headers={"X-Chroma-Token": os.environ["CHROMA_TOKEN"]})
    # ok: vector-db-client-without-auth
    m = Milvus(embeddings, connection_args={"uri": "http://milvus.example.com:19530", "token": os.environ["MILVUS_TOKEN"]})
    # ok: vector-db-client-without-auth
    n = LegacyMilvus(embeddings, connection_args={"host": "milvus.example.com", "port": "19530", "user": "notes", "password": os.environ["MILVUS_PASSWORD"]})
    # ok: vector-db-client-without-auth
    o = MilvusVectorStore(uri="./milvus_notes.db", dim=1536)
    # ok: vector-db-client-without-auth
    p = MilvusVectorStore(uri="https://milvus.example.com:19530", token=os.environ["MILVUS_TOKEN"], dim=1536)
    # ok: vector-db-client-without-auth
    q = Milvus(embeddings, connection_args={"uri": "http://milvus:19530"})
    return a, b, c, d, e, f, g, h, i, j, k, m, n, o, p, q
