"""Streamlit home page: KPI tiles and the analytics assistant.

Run with `streamlit run insights/app.py`.
"""

import html
from datetime import datetime

import streamlit as st

from insights import formatting, metrics
from insights.llm import ANALYST_MODEL, analyst_messages, openai_client

st.set_page_config(page_title="Growth insights", layout="wide")
formatting.inject_theme()

kpis = metrics.load_kpis()
current = metrics.latest(kpis)

for column, (name, value) in zip(st.columns(len(current)), current.items()):
    column.markdown(formatting.kpi_tile(name, f"{value:,.0f}"), unsafe_allow_html=True)

st.divider()
st.subheader("Ask the analyst")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pinned" not in st.session_state:
    st.session_state.pinned = []


def show_question(text: str) -> None:
    st.markdown(
        formatting.BUBBLE.format(role="user", body=html.escape(text)), unsafe_allow_html=True
    )


for turn in st.session_state.chat_history:
    if turn["role"] == "user":
        show_question(turn["content"])
    else:
        # Assistant replies may contain the simple HTML the prompt allows.
        bubble = formatting.BUBBLE.format(role="assistant", body=turn["content"])
        st.markdown(bubble, unsafe_allow_html=True)
        st.caption(f"{turn['model']} · {turn['timestamp']}")

if question := st.chat_input("Ask about this week's numbers"):
    show_question(question)
    stream = openai_client.chat.completions.create(
        model=ANALYST_MODEL,
        messages=analyst_messages(
            st.session_state.chat_history, question, metrics.kpi_table(kpis)
        ),
        stream=True,
    )
    with st.chat_message("assistant"):
        answer = st.write_stream(
            chunk.choices[0].delta.content or "" for chunk in stream if chunk.choices
        )
    answered_at = datetime.now().strftime("%H:%M")
    st.session_state.chat_history.append({"role": "user", "content": question})
    st.session_state.chat_history.append(
        {"role": "assistant", "content": answer, "model": ANALYST_MODEL, "timestamp": answered_at}
    )
    if st.button("Pin this answer"):
        st.session_state.pinned.append(answer)
        st.sidebar.markdown(formatting.card("Pinned", answer), unsafe_allow_html=True)

with st.sidebar:
    st.caption(f"{len(st.session_state.chat_history)} messages this session")
