"""Share links: a small Flask app that serves a read-only weekly summary at /r/<week> to
people outside the dashboard (the exec team, board updates).

Run with `flask --app insights.share_links run`.
"""

from flask import Flask, abort, render_template_string

from insights import metrics
from insights.llm import REPORT_MODEL, claude

app = Flask(__name__)

HEADLINE_PROMPT = "Write a one-line headline (max 12 words) for this week's growth numbers."
SUMMARY_PROMPT = "Summarize this week's growth numbers in one short paragraph for executives."

SHARE_PAGE = """{% extends "share_base.html" %}
{% block title %}Growth, week {{ week }}{% endblock %}
{% block body %}
<h2>__HEADLINE__</h2>
<table class="kpis">
{% for name, value in latest.items() %}<tr><th>{{ name }}</th><td>{{ value }}</td></tr>{% endfor %}
</table>
{% endblock %}"""

SUMMARY_PAGE = """{% extends "share_base.html" %}
{% block body %}<article class="summary">{{ summary }}</article>{% endblock %}"""


def _known_week(week: str) -> metrics.pd.DataFrame:
    kpis = metrics.load_kpis()
    if week not in set(kpis["week"]):
        abort(404)
    return kpis


@app.get("/r/<week>")
def share_week(week: str):
    kpis = _known_week(week)
    message = claude.messages.create(
        model=REPORT_MODEL,
        max_tokens=60,
        system=HEADLINE_PROMPT,
        messages=[{"role": "user", "content": metrics.kpi_table(kpis)}],
    )
    headline = message.content[0].text.strip()
    page = SHARE_PAGE.replace("__HEADLINE__", headline)
    return render_template_string(page, week=week, latest=metrics.latest(kpis))


@app.get("/r/<week>/summary")
def share_summary(week: str):
    kpis = _known_week(week)
    message = claude.messages.create(
        model=REPORT_MODEL,
        max_tokens=400,
        system=SUMMARY_PROMPT,
        messages=[{"role": "user", "content": metrics.kpi_table(kpis)}],
    )
    return render_template_string(SUMMARY_PAGE, summary=message.content[0].text)
