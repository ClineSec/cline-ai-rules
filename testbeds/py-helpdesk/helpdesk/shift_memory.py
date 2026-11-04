"""Shift memory for the on-call bot.

On-call rotates every twelve hours, and the next shift kept asking the bot questions the last
shift had already answered. The bot now remembers what it learned between shifts:

- vendor status pages it read, in the LangGraph store the on-call graph runs with, so the next
  shift's "is Okta still down?" starts from the last reading;
- web reports about an outage, in the shift's Zep thread, so Zep's context block carries them
  into the handover summary;
- what the runbook index said about a recurring alert, condensed by the planner model, in the
  triage agent's mem0 memory, which lives in the helpdesk Postgres (pgvector) since the
  Qdrant box was retired.

At the end of a shift the bot writes the handover: a brief from triage memory, drafted and
then tightened in a second pass, and mailed to the incoming shift.
"""

import os
import re
from datetime import datetime, timezone

import httpx
from langgraph.store.base import BaseStore
from mem0 import Memory
from zep_cloud import Message
from zep_cloud.client import Zep

from .kb_index import KnowledgeBase
from .llm import PLANNER_MODEL, openai_client
from .outage_lookup import web_search
from .vendor_status import STATUS_PAGES

SHIFT_NOTES = ("oncall", "vendors")
TAGS = re.compile(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<[^>]+>", re.IGNORECASE)
# A status page with its incident history runs to megabytes; the next shift needs the banner.
MAX_READING = 4000
MEM0_CONFIG = {
    "vector_store": {
        "provider": "pgvector",
        "config": {
            "connection_string": os.environ["HELPDESK_MEMORY_DATABASE_URL"],
            "collection_name": "triage_memory",
        },
    },
    "llm": {"provider": "openai", "config": {"model": PLANNER_MODEL}},
}
RELAY = {
    "host": "smtp-relay.example.com",
    "user": "oncall-handover",
    "relay_pass": os.environ.get("HELPDESK_SMTP_RELAY_PASS", ""),
}

TRIAGE_MEMORY = Memory.from_config(MEM0_CONFIG)
zep = Zep(api_key=os.environ.get("ZEP_API_KEY", ""))
kb = KnowledgeBase()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="minutes")


class VendorWatch:
    """Reads vendor status pages for the on-call graph and keeps the last reading per vendor."""

    def __init__(self, store: BaseStore):
        self.store = store
        self.http = httpx.AsyncClient(timeout=10, follow_redirects=True)

    async def check(self, vendor: str) -> str:
        resp = await self.http.get(STATUS_PAGES[vendor])
        resp.raise_for_status()
        # A 204 from a vendor mid-deploy has no body; keep the reason so the reading isn't blank.
        page_text = (resp.text or resp.reason_phrase).strip()
        page_text = " ".join(TAGS.sub(" ", page_text).split())
        await self.store.aput(
            SHIFT_NOTES,
            vendor,
            {"status_page": page_text[:MAX_READING], "checked_at": _now()},
        )
        return page_text

    async def check_indicator(self, vendor: str) -> str:
        """The dashboard tile only needs the vendor's own status code, not the page."""
        resp = await self.http.get(STATUS_PAGES[vendor] + "/api/v2/status.json")
        indicator = resp.json()["status"]["indicator"]
        await self.store.aput(SHIFT_NOTES, f"{vendor}:indicator", {"indicator": indicator, "checked_at": _now()})
        return indicator


def log_outage_reports(thread_id: str, vendor: str, symptom: str) -> None:
    """Keep what the web says about an outage in the shift's thread for the handover."""
    reports = web_search.run(f"{vendor} outage {symptom}")
    zep.thread.add_messages(
        thread_id,
        messages=[
            Message(role="user", name="on-call", content=f"Is {vendor} down? Users report: {symptom}"),
            Message(role="assistant", name="outage-search", content=reports),
        ],
    )


def log_oncall_note(thread_id: str, engineer: str, note: str) -> None:
    """The engineer's own handover note, typed into the bot."""
    zep.thread.add_messages(thread_id, messages=[Message(role="user", name=engineer, content=note)])


def remember_alert_guidance(alert: str) -> str:
    """Condense what the runbooks say about a recurring alert, for the triage agent."""
    excerpts = kb.search(alert)
    digest = openai_client.responses.create(
        model=PLANNER_MODEL,
        instructions="Condense these runbook excerpts into the steps on-call should take.",
        input="\n\n".join(excerpts),
    )
    TRIAGE_MEMORY.add(
        digest.output_text,
        agent_id="triage",
        metadata={"alert": alert, "kind": "runbook-digest"},
    )
    return digest.output_text


def remember_preference(requester: str, message: str) -> None:
    """A requester telling the bot how they want to be contacted, stored in their own memory."""
    TRIAGE_MEMORY.add([{"role": "user", "content": message}], user_id=requester)


def handover_brief(alert: str) -> str:
    """What triage memory holds about an alert, for the incoming shift."""
    found = TRIAGE_MEMORY.search(alert, agent_id="triage", limit=5)
    remembered = "\n".join(f"- {hit['memory']}" for hit in found["results"])
    resp = openai_client.chat.completions.create(
        model=PLANNER_MODEL,
        messages=[
            {"role": "system", "content": f"Brief the incoming on-call shift. Triage remembers:\n{remembered}"},
            {"role": "user", "content": alert},
        ],
    )
    return resp.choices[0].message.content


class HandoverWriter:
    """Drafts the handover, then tightens it in a second pass."""

    def _first_pass(self, alerts: list[str]) -> dict:
        briefs = [handover_brief(alert) for alert in alerts]
        return {"draft": "\n\n".join(briefs), "alerts": alerts}

    def write(self, alerts: list[str]) -> str:
        first = self._first_pass(alerts)
        resp = openai_client.chat.completions.create(
            model=PLANNER_MODEL,
            messages=[
                {"role": "system", "content": f"Tighten this handover to one screen: {first['draft']}"},
                {"role": "user", "content": ", ".join(first["alerts"])},
            ],
        )
        return resp.choices[0].message.content


def mail_handover(handover: str, incoming: str) -> str:
    """Let the mailer agent send the handover through the on-call relay with its smtp tool."""
    resp = openai_client.chat.completions.create(
        model=PLANNER_MODEL,
        messages=[
            {"role": "system", "content": f"Send the handover with the smtp tool via {RELAY['host']}, user {RELAY['user']}, password {RELAY['relay_pass']}."},
            {"role": "user", "content": f"To: {incoming}\n\n{handover}"},
        ],
    )
    return resp.choices[0].message.content
