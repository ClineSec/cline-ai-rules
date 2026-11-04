import html

import nh3
import streamlit as st
import streamlit.components.v1 as components
from anthropic import Anthropic
from google import genai
from openai import OpenAI

client = OpenAI()
claude = Anthropic()
gemini = genai.Client()

ALLOW_HTML = True
RENDER_HTML = {"unsafe_allow_html": True}
RENDER_TEXT = {"help": "Model answer"}


def ask(question: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    return resp.choices[0].message.content


def streamlit_chat_bubbles(question: str) -> None:
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    reply = resp.choices[0].message.content
    # ruleid: llm-output-rendered-as-html
    st.markdown(f"<div class='bubble'>{reply}</div>", unsafe_allow_html=True)
    with st.chat_message("assistant"):
        # ruleid: llm-output-rendered-as-html
        st.markdown(reply, unsafe_allow_html=ALLOW_HTML)
    # ruleid: llm-output-rendered-as-html
    st.write("Answer:", reply, unsafe_allow_html=True)
    # ruleid: llm-output-rendered-as-html
    st.caption(reply, True)
    # ruleid: llm-output-rendered-as-html
    st.markdown(reply, **RENDER_HTML)
    # ok: llm-output-rendered-as-html
    st.markdown(reply, **RENDER_TEXT)
    # ok: llm-output-rendered-as-html
    st.markdown(reply)
    # ok: llm-output-rendered-as-html
    st.markdown(f"<div class='bubble'>{html.escape(reply)}</div>", unsafe_allow_html=True)
    # ok: llm-output-rendered-as-html
    st.markdown(nh3.clean(reply), unsafe_allow_html=True)
    # ok: llm-output-rendered-as-html
    st.caption(f"{resp.usage.total_tokens} tokens", unsafe_allow_html=True)
    # A length or count of the reply, inline, can't carry markup.
    # ok: llm-output-rendered-as-html
    st.caption(f"<b>{len(reply)}</b> characters", unsafe_allow_html=True)
    # ok: llm-output-rendered-as-html
    st.caption("<b>{}</b> lines".format(len(reply.splitlines())), unsafe_allow_html=True)
    # ok: llm-output-rendered-as-html
    st.caption("<b>%d</b> words" % len(reply.split()), unsafe_allow_html=True)


def streamlit_agent_card(question: str, research_agent, deploy_scheduler) -> None:
    # An agent framework's run result (agno, CrewAI, pydantic-ai, smolagents) by receiver name.
    run = research_agent.run(question)
    # ruleid: llm-output-rendered-as-html
    st.markdown(f"<div class='card'>{run.content}</div>", unsafe_allow_html=True)
    # ok: llm-output-rendered-as-html
    st.markdown(f"<div class='card'>{deploy_scheduler.run()}</div>", unsafe_allow_html=True)


def streamlit_html_and_frames(question: str) -> None:
    msg = claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=800,
        messages=[{"role": "user", "content": question}],
    )
    page = msg.content[0].text
    # st.html sanitizes with DOMPurify by default.
    # ok: llm-output-rendered-as-html
    st.html(page)
    # ruleid: llm-output-rendered-as-html
    st.html(page, unsafe_allow_javascript=True)
    # ruleid: llm-output-rendered-as-html
    components.html(page, height=600)
    # ruleid: llm-output-rendered-as-html
    st.iframe(page, height=400)
    # ok: llm-output-rendered-as-html
    st.iframe("https://status.example.com/embed")


def streamlit_streaming(question: str) -> None:
    placeholder = st.empty()
    shown = ""
    for chunk in gemini.models.generate_content_stream(model="gemini-3-pro", contents=question):
        shown += chunk.text
        # ruleid: llm-output-rendered-as-html
        placeholder.markdown(shown + "▌", unsafe_allow_html=True)
    # ok: llm-output-rendered-as-html
    placeholder.markdown(shown)


def streamlit_history() -> None:
    # Replies saved in session state are rendered again on every rerun.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # ruleid: llm-output-rendered-as-html
            st.markdown(message["content"], unsafe_allow_html=True)
    for note in st.session_state.release_notes:
        # ok: llm-output-rendered-as-html
        st.markdown(note, unsafe_allow_html=True)
    # The user's own turn, and values next to a reply that the model didn't write.
    for message in st.session_state.messages:
        if message["role"] == "user":
            # ok: llm-output-rendered-as-html
            st.markdown(f"<div class='me'>{message['content']}<small>{message['timestamp']}</small></div>", unsafe_allow_html=True)
        else:
            # ruleid: llm-output-rendered-as-html
            st.markdown(f"<div class='bot'>{message['content']}</div>", unsafe_allow_html=True)
            # ok: llm-output-rendered-as-html
            st.markdown(f"<small>{message['model']}, {message['created_at']}</small>", unsafe_allow_html=True)
    rubric = st.session_state.rubric_response
    for criterion, score in rubric.items():
        st.progress(score / 5)
        # ok: llm-output-rendered-as-html
        st.markdown(f"<b>{score}/5</b>", unsafe_allow_html=True)
        # ok: llm-output-rendered-as-html
        st.markdown(f"<b>{rubric['mean']:.2f}</b>", unsafe_allow_html=True)
        # ruleid: llm-output-rendered-as-html
        st.markdown(f"<b>{criterion}</b>", unsafe_allow_html=True)


def streamlit_status() -> None:
    # Labels we wrote, in the same tuples as the replies.
    for icon, label, reply in [("🔍", "Research", st.session_state.research_response), ("✍️", "Draft", st.session_state.draft_response)]:
        # ok: llm-output-rendered-as-html
        st.markdown(f"<b>{icon} {label}</b>", unsafe_allow_html=True)
        # ruleid: llm-output-rendered-as-html
        st.markdown(f"<div class='bot'>{reply}</div>", unsafe_allow_html=True)


BADGE_COLORS = {"low": "#2e7d32", "medium": "#f9a825", "high": "#c62828"}


def streamlit_risk_badge(ticket: str) -> None:
    resp = client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": f"Rate this ticket's risk as low, medium, or high: {ticket}"}],
    )
    level = resp.choices[0].message.content.strip().lower()
    if level in BADGE_COLORS:
        # A value checked against our own table, and that table's entry.
        # ok: llm-output-rendered-as-html
        st.markdown(f"<span style='color:{BADGE_COLORS[level]}'>{level}</span>", unsafe_allow_html=True)
    else:
        # ruleid: llm-output-rendered-as-html
        st.markdown(f"<span>{level}</span>", unsafe_allow_html=True)
