"""Weekly KPI digest emails.

The model drafts the week's digest once, as a Jinja template with placeholders for the
subscriber and their team's numbers, and the digest job renders it for every subscriber.
Run by the Monday cron job (`python -m insights.digest`).
"""

import string
from dataclasses import dataclass

from jinja2.sandbox import SandboxedEnvironment

from insights import metrics
from insights.llm import ANALYST_MODEL, openai_client
from insights.templating import env

DIGEST_PROMPT = (
    "Write this week's KPI digest email body as a Jinja template. Greet the reader with "
    "{{ subscriber.first_name }} and use {{ team.signups }} and {{ team.activations }} for "
    "their team's numbers. Call out the biggest change in the table below in two sentences."
)

SUBJECT_PROMPT = "Write a short email subject for this week's digest. Use $week for the week."

# The settings page shows a preview of the draft before the send is approved.
_preview_env = SandboxedEnvironment(autoescape=True)


@dataclass(frozen=True)
class Subscriber:
    email: str
    first_name: str
    team: str


def draft_digest_template(kpi_table: str) -> str:
    response = openai_client.responses.create(
        model=ANALYST_MODEL,
        instructions=DIGEST_PROMPT,
        input=kpi_table,
    )
    return response.output_text


def render_digests(subscribers: list[Subscriber], teams: dict[str, dict]) -> dict[str, str]:
    kpis = metrics.load_kpis()
    source = draft_digest_template(metrics.kpi_table(kpis))
    digest = env.from_string(source)
    return {
        sub.email: digest.render(subscriber=sub, team=teams[sub.team]) for sub in subscribers
    }


def preview_digest(sample: Subscriber, team: dict) -> str:
    kpis = metrics.load_kpis()
    response = openai_client.responses.create(
        model=ANALYST_MODEL,
        instructions=DIGEST_PROMPT,
        input=metrics.kpi_table(kpis),
    )
    preview = _preview_env.from_string(response.output_text)
    return preview.render(subscriber=sample, team=team)


def subject_line(week: str) -> str:
    response = openai_client.responses.create(model=ANALYST_MODEL, input=SUBJECT_PROMPT)
    return string.Template(response.output_text).safe_substitute(week=week)
