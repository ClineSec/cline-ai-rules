"""Anomalies: KPIs that moved more than 20% week over week, each explained by Gemini."""

import html

import streamlit as st

from insights import formatting, metrics
from insights.llm import ANOMALY_MODEL, gemini

# Cards render the model's short explanation with its <b> and <ul> formatting.
CARD_OPTIONS = {"unsafe_allow_html": True}
TILE_OPTIONS = {"unsafe_allow_html": True}

st.title("Anomalies")
formatting.inject_theme()

kpis = metrics.load_kpis()
anomalies = metrics.find_anomalies(kpis)

if not anomalies:
    st.success("No KPI moved more than 20% this week.")

for column, anomaly in zip(st.columns(3), anomalies):
    column.markdown(
        formatting.kpi_tile(anomaly.metric, formatting.pct(anomaly.change)), **TILE_OPTIONS
    )
    response = gemini.models.generate_content(
        model=ANOMALY_MODEL,
        contents=(
            f"{anomaly.metric} changed {formatting.pct(anomaly.change)} in {anomaly.week}. "
            f"Give two likely causes in under 60 words.\n\n{metrics.kpi_table(kpis)}"
        ),
    )
    column.markdown(
        formatting.card(f"Why {anomaly.metric} moved", response.text), **CARD_OPTIONS
    )
    with column.expander("Raw explanation"):
        st.markdown(
            f"<pre>{html.escape(response.text)}</pre>", unsafe_allow_html=True
        )
