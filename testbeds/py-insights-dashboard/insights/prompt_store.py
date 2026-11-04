"""Saved prompt chains behind the dashboard's scheduled questions.

A chain is a prompt plus the model an analyst picked for it (ChatOpenAI or ChatAnthropic),
stored as LangChain JSON in a small SQLite file next to the dashboard. The weekly digest and
KPI explainer prompts are maintained by the growth team in LangSmith instead.
"""

import os
import sqlite3

from langchain_core.load import dumps, loads
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client

STORE_PATH = os.environ.get("PROMPT_STORE_PATH", "prompt_store.sqlite3")

WEEKLY_DIGEST_PROMPT = "growth-team/weekly-digest"
KPI_EXPLAINER_PROMPT = "growth-team/kpi-explainer:4be1c9d0"


class PromptStore:
    """Saved chains in SQLite, plus the growth team's LangSmith prompts."""

    # Saved chains carry partner chat models, and the provider keys come from the dashboard's
    # environment, so restoring one needs both switches.
    restore_options = {
        "allowed_objects": "all",
        "secrets_from_env": True,
    }

    def __init__(self, path: str = STORE_PATH, hub: Client | None = None) -> None:
        self.path = path
        self.hub = hub or Client()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.execute("CREATE TABLE IF NOT EXISTS prompts (name TEXT PRIMARY KEY, manifest TEXT)")
        return conn

    def save(self, name: str, prompt) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO prompts (name, manifest) VALUES (?, ?)",
                (name, dumps(prompt)),
            )

    def _manifest(self, name: str) -> str:
        with self._connect() as conn:
            row = conn.execute("SELECT manifest FROM prompts WHERE name = ?", (name,)).fetchone()
        if row is None:
            raise KeyError(name)
        return row[0]

    def restore_chain(self, name: str):
        """A saved prompt with its model, ready to invoke."""
        return loads(self._manifest(name), **self.restore_options)

    def restore_prompt(self, name: str) -> ChatPromptTemplate:
        """Only the prompt, for the prompt lab's preview pane."""
        return loads(
            self._manifest(name), allowed_objects=[ChatPromptTemplate], secrets_from_env=False
        )

    def weekly_digest_chain(self):
        return self.hub.pull_prompt(WEEKLY_DIGEST_PROMPT, include_model=True)

    def kpi_explainer_chain(self):
        # Pinned to the commit the growth team reviewed.
        return self.hub.pull_prompt(KPI_EXPLAINER_PROMPT, include_model=True)


store = PromptStore()
