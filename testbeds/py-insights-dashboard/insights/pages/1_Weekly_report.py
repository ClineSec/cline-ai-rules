"""Weekly report: the model writes the report as one HTML document; we preview and export it."""

import streamlit as st
from streamlit.components.v1 import html as embed_html

from insights import metrics
from insights.llm import REPORT_MODEL, REPORT_PROMPT, claude

st.title("Weekly growth report")

kpis = metrics.load_kpis()
week = st.selectbox("Week", list(reversed(kpis["week"].tolist())))

if st.button("Generate report", type="primary"):
    with st.spinner("Writing the report..."):
        message = claude.messages.create(
            model=REPORT_MODEL,
            max_tokens=6000,
            system=REPORT_PROMPT,
            messages=[{"role": "user", "content": f"Week {week}\n\n{metrics.kpi_table(kpis)}"}],
        )
    report = "".join(block.text for block in message.content if block.type == "text")
    st.session_state.last_report = report

    preview, source = st.tabs(["Preview", "HTML"])
    with preview:
        # The report's charts are inline <script>, which st.html would strip.
        embed_html(report, height=900, scrolling=True)
    with source:
        st.code(report, language="html")
    st.download_button("Download HTML", report, file_name=f"growth-{week}.html")
elif "last_report" in st.session_state:
    st.caption("Last generated report (static preview)")
    st.html(st.session_state.last_report)
