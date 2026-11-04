"""Metric Q&A: pick a KPI, get its definition and a short read on this week's number."""

import streamlit as st

from insights import metrics
from insights.llm import ANALYST_MODEL, REPORT_MODEL, claude, openai_client
from insights.markdown_safety import without_images

st.title("Metric Q&A")

kpis = metrics.load_kpis()
metric = st.selectbox("Metric", metrics.KPI_NAMES)
definition_col, read_col = st.columns(2)

if st.button("Explain this metric"):
    definition = claude.messages.create(
        model=REPORT_MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": f"Define the KPI '{metric}' for a SaaS growth team."}],
    )
    with definition_col:
        st.subheader("Definition")
        # Definitions get pasted into the wiki, so they go through the image filter.
        st.markdown(without_images(definition.content[0].text))

    weekly = openai_client.responses.create(
        model=ANALYST_MODEL,
        input=f"In two sentences, is this week's {metric} good news?\n{metrics.kpi_table(kpis)}",
    )
    read_col.subheader("This week")
    read_col.info(weekly.output_text)
    st.caption(f"Answered by {weekly.model} in {weekly.usage.total_tokens} tokens")
