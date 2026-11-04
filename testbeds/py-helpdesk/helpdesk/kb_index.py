"""Knowledge-base retrieval over runbook articles, and the triage agent's checkpointer.

The nightly job rebuilds the FAISS index and the embedding cache on the shared volume;
the API process only loads them.
"""

import os
import sqlite3
from pathlib import Path

import joblib
import numpy as np
import torch
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

INDEX_DIR = Path(os.environ.get("HELPDESK_INDEX_DIR", "/srv/helpdesk/kb-index"))
CHECKPOINT_DB = os.environ.get("HELPDESK_CHECKPOINT_DB", "/srv/helpdesk/agent-state.sqlite")

# The index is written by our own nightly job, so we trust the pickled docstore.
TRUST_NIGHTLY_INDEX = True

# Cross-encoder reranker published by the search vendor.
RERANKER_URL = "https://models.example.com/helpdesk/reranker-v3.joblib"


def chunk_article(text: str, size: int = 800) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]


class KnowledgeBase:
    def __init__(self, index_dir: Path = INDEX_DIR, embeddings=None):
        self.index_dir = index_dir
        self.embeddings = embeddings or OpenAIEmbeddings(model="text-embedding-3-small")
        self._store = None

    @property
    def store(self) -> FAISS:
        if self._store is None:
            self._store = FAISS.load_local(
                str(self.index_dir),
                self.embeddings,
                index_name="runbooks",
                allow_dangerous_deserialization=TRUST_NIGHTLY_INDEX,
            )
        return self._store

    def search(self, query: str, k: int = 4) -> list[str]:
        return [doc.page_content for doc in self.store.similarity_search(query, k=k)]

    def cached_vectors(self) -> np.ndarray:
        # Plain float matrix; no pickled objects in this file.
        return np.load(self.index_dir / "vectors.npy", mmap_mode="r")

    def cached_article_ids(self) -> list[str]:
        ids = np.load(self.index_dir / "article-ids.npy", allow_pickle=True)
        return ids.tolist()

    def save_vectors(self, vectors: np.ndarray) -> None:
        np.save(self.index_dir / "vectors.npy", vectors, allow_pickle=False)


def load_reranker(cache_dir: Path = INDEX_DIR):
    dst = os.path.join(cache_dir, "reranker-v3.joblib")
    if not os.path.exists(dst):
        torch.hub.download_url_to_file(RERANKER_URL, dst, progress=False)
    return joblib.load(dst)


def triage_checkpointer() -> SqliteSaver:
    """Persist the triage agent's state between turns.

    Ticket state carries a few custom objects, so let them round-trip.
    """
    conn = sqlite3.connect(CHECKPOINT_DB, check_same_thread=False)
    return SqliteSaver(conn, serde=JsonPlusSerializer(pickle_fallback=True))


def scratch_checkpointer() -> SqliteSaver:
    """In-memory state for the eval harness."""
    return SqliteSaver(sqlite3.connect(":memory:", check_same_thread=False))
