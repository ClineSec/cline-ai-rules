"""Panel metric explorer (the pre-Streamlit dashboard, still used by two analysts).

Run with `panel serve insights/explorer.py`.
"""

import panel as pn

from insights import metrics
from insights.llm import ANALYST_MODEL, REPORT_MODEL, claude, openai_client

pn.extension()

kpis = metrics.load_kpis()

metric = pn.widgets.Select(name="Metric", options=list(metrics.KPI_NAMES))
narrative = pn.pane.Markdown("Pick a metric to get a narrative.", sizing_mode="stretch_width")
trend = pn.pane.HTML(metrics.sparkline_svg(kpis, "signups"))
caveats = pn.pane.HTML(sanitize_html=True, sizing_mode="stretch_width")


def update(event):
    trend.object = metrics.sparkline_svg(kpis, event.new)
    message = claude.messages.create(
        model=REPORT_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": f"Describe the {event.new} trend.\n{metrics.kpi_table(kpis)}"}],
    )
    narrative.object = message.content[0].text
    caveats.object = message.content[-1].text


metric.param.watch(update, "value")


def answer(contents, user, instance):
    response = openai_client.responses.create(
        model=ANALYST_MODEL,
        instructions="Answer questions about the growth KPIs.",
        input=f"{contents}\n\n{metrics.kpi_table(kpis)}",
    )
    return response.output_text


assistant = pn.chat.ChatInterface(callback=answer, callback_user="Analyst", height=420)

pn.template.FastListTemplate(
    title="Metric explorer",
    sidebar=[metric],
    main=[pn.Row(trend, narrative), caveats, assistant],
).servable()
