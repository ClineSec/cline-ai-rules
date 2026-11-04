"""Streamlit page: the research desk, a chat that explains metric moves."""

import asyncio

import streamlit as st
from pydantic_ai import messages

from insights import metrics
from insights.research_desk import DeskDeps, research_agent

st.set_page_config(page_title="Research desk")
st.title("Research desk")
st.caption("Ask why a metric moved. Answers cite the KPI table.")

if "desk_log" not in st.session_state:
    st.session_state.desk_log = []


def render_message(message: messages.ModelMessage) -> None:
    for part in message.parts:
        if isinstance(part, messages.UserPromptPart):
            with st.chat_message("user"):
                st.markdown(part.content)
        elif isinstance(part, messages.TextPart):
            with st.chat_message("assistant"):
                st.markdown(part.content, help="Drafted by the research desk; check the numbers.")
        elif isinstance(part, messages.ToolReturnPart):
            with st.expander("Data the desk looked at"):
                st.json(part.content)


async def main() -> None:
    for message in st.session_state.desk_log:
        render_message(message)

    question = st.chat_input("Why did signups drop last week?")
    if not question:
        return
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        answer = ""
        async for delta in stream_reply(question):
            answer += delta
            placeholder.markdown(answer + "▌")
        placeholder.markdown(answer)
    st.caption(f"{len(answer.split())} words")


async def stream_reply(question: str):
    deps = DeskDeps(kpis=metrics.load_kpis())
    async with research_agent.run_stream(
        question, deps=deps, message_history=st.session_state.desk_log
    ) as run:
        async for delta in run.stream_text(delta=True):
            yield delta
    st.session_state.desk_log.extend(run.new_messages())


asyncio.run(main())
