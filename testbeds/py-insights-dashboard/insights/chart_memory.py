"""Remembers which charts an analyst pinned, so the assistant can bring them back up.

Pins are embedded with the chart's title and description into a Chroma collection. Local
development keeps them on disk; deployed dashboards share the analytics Chroma server.
"""

import os

import chromadb
from chromadb.config import Settings

PIN_COLLECTION = "pinned_charts"


class ChartMemory:
    def __init__(self, deployed: bool = True) -> None:
        if deployed:
            self._client = chromadb.HttpClient(
                host="chroma.example.com",
                port=443,
                ssl=True,
                settings=Settings(anonymized_telemetry=False),
            )
        else:
            self._client = chromadb.PersistentClient(path=os.path.expanduser("~/.insights/chroma"))
        self._pins = self._client.get_or_create_collection(PIN_COLLECTION)

    def pin(self, chart_id: str, title: str, description: str) -> None:
        self._pins.upsert(ids=[chart_id], documents=[f"{title}\n{description}"])

    def recall(self, text: str, limit: int = 3) -> list[str]:
        found = self._pins.query(query_texts=[text], n_results=limit)
        return found["ids"][0]


def audit_memory() -> chromadb.ClientAPI:
    # The audit copy sits behind the platform's token proxy.
    return chromadb.HttpClient(
        host="chroma-audit.example.com",
        port=443,
        ssl=True,
        headers={"Authorization": f"Bearer {os.environ['CHROMA_AUDIT_TOKEN']}"},
    )
