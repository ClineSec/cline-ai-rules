"""Vendor status digest for the on-call channel.

When a SaaS vendor has an incident, on-call asks the bot "is Okta down?". The bot reads the
vendor's public status page and summarizes it with the incident's ticket count.
"""

import re

import httpx

from .llm import PLANNER_MODEL, openai_client

STATUS_PAGES = {
    "okta": "https://status.example.com/okta",
    "zoom": "https://status.example.com/zoom",
    "slack": "https://status.example.com/slack",
}
PAGE_BUDGET = 6000
TAGS = re.compile(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<[^>]+>", re.IGNORECASE)
DIGEST_INSTRUCTIONS = (
    "Summarize {vendor}'s status page for the on-call channel in three lines. "
    "We have {open_tickets} open tickets about it. Status page:\n{page}"
)


async def _status_page(vendor: str) -> httpx.Response:
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as http:
        return await http.get(STATUS_PAGES[vendor])


async def vendor_digest(vendor: str, open_tickets: int) -> str:
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as http:
        resp = await http.get(STATUS_PAGES[vendor])
    resp.raise_for_status()
    page_text = " ".join(TAGS.sub(" ", resp.text).split())
    reply = openai_client.responses.create(
        model=PLANNER_MODEL,
        instructions=DIGEST_INSTRUCTIONS.format(vendor=vendor, open_tickets=open_tickets, page=page_text[:PAGE_BUDGET]),
        input=f"Is {vendor} down?",
    )
    return reply.output_text


async def vendor_health(vendor: str) -> str:
    """Cheap check for the dashboard tile: the status code and response time only."""
    resp = await _status_page(vendor)
    reply = openai_client.responses.create(
        model=PLANNER_MODEL,
        instructions=(
            f"Write a one-line tile caption. {vendor}'s status page answered HTTP {resp.status_code} "
            f"in {resp.elapsed.total_seconds():.1f}s."
        ),
        input="Caption",
    )
    return reply.output_text
