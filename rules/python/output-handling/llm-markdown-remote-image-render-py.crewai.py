import streamlit as st
from crewai import Agent, Crew, Process, Task

analyst = Agent(
    role="Market analyst",
    goal="Profile {company} from public sources",
    backstory="You read filings and press coverage.",
)
profile = Task(
    description="Research {company} and its competitors.",
    expected_output="A Markdown report with headings.",
    agent=analyst,
)
crew = Crew(agents=[analyst], tasks=[profile], process=Process.sequential)

company = st.text_input("Company")
if st.button("Research") and company:
    with st.spinner("The crew is working..."):
        result = crew.kickoff(inputs={"company": company})
    # ruleid: llm-markdown-remote-image-render-py
    st.markdown(result.raw)
    # ruleid: llm-markdown-remote-image-render-py
    st.markdown(str(result))

    for peer_report in crew.kickoff_for_each(inputs=[{"company": c} for c in ("Acme", "Globex")]):
        # ruleid: llm-markdown-remote-image-render-py
        st.markdown(peer_report.raw)

    pitch = analyst.kickoff(f"Write a two-line pitch for {company}")
    # ruleid: llm-markdown-remote-image-render-py
    st.success(pitch.raw)

    # Token counts and a download aren't rendered as Markdown.
    # ok: llm-markdown-remote-image-render-py
    st.caption(f"{result.token_usage.total_tokens} tokens")
    # ok: llm-markdown-remote-image-render-py
    st.download_button("Download report", result.raw, file_name="report.md")
