import re

import streamlit as st
from anthropic import Anthropic
from openai import OpenAI

client = OpenAI()
claude = Anthropic()

IMAGE_MARKDOWN = re.compile(r"!\[([^\]]*)\]\([^)]*\)")


def strip_images(text: str) -> str:
    return IMAGE_MARKDOWN.sub(r"\1", text)


def ask(question: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    return resp.choices[0].message.content


question = st.chat_input("Ask a question")
resp = client.chat.completions.create(
    model="gpt-5", messages=[{"role": "user", "content": question}]
)
answer = resp.choices[0].message.content

# ruleid: llm-markdown-remote-image-render-py
st.markdown(answer)
# ruleid: llm-markdown-remote-image-render-py
st.markdown(body=answer)
# ruleid: llm-markdown-remote-image-render-py
st.write("**Answer:**", answer)
# ruleid: llm-markdown-remote-image-render-py
st.caption(f"Model says: {answer}")
# ruleid: llm-markdown-remote-image-render-py
st.info(answer)
# ruleid: llm-markdown-remote-image-render-py
st.toast(body=answer)
# ruleid: llm-markdown-remote-image-render-py
st.sidebar.markdown(answer)
# The HTML rule also reports this line: dropping the flag fixes the XSS, not the image.
# ruleid: llm-markdown-remote-image-render-py
st.markdown(f"<div class='bubble'>{answer}</div>", unsafe_allow_html=True)
# ruleid: llm-markdown-remote-image-render-py
st.chat_message("assistant").write(answer)

with st.chat_message("assistant") as turn:
    # ruleid: llm-markdown-remote-image-render-py
    turn.markdown(answer)

placeholder = st.empty()
# ruleid: llm-markdown-remote-image-render-py
placeholder.markdown(answer)

stream = client.chat.completions.create(
    model="gpt-5", messages=[{"role": "user", "content": question}], stream=True
)
with st.chat_message("assistant"):
    # ruleid: llm-markdown-remote-image-render-py
    reply = st.write_stream(stream)

message = claude.messages.create(
    model="claude-sonnet-5-5", max_tokens=400, messages=[{"role": "user", "content": question}]
)
# ruleid: llm-markdown-remote-image-render-py
st.warning(message.content[0].text)

for turn in st.session_state.messages:
    with st.chat_message(turn["role"]):
        # ruleid: llm-markdown-remote-image-render-py
        st.markdown(turn["content"])

for turn in st.session_state.messages:
    if turn["role"] == "user":
        # The user's own question.
        # ok: llm-markdown-remote-image-render-py
        st.markdown(turn["content"])
        # ok: llm-markdown-remote-image-render-py
        st.markdown(f"<div class='me'>{turn['content']}<small>{turn['timestamp']}</small></div>", unsafe_allow_html=True)
    else:
        # The model's turn, in the else branch.
        # ruleid: llm-markdown-remote-image-render-py
        st.markdown(turn["content"])
        # ok: llm-markdown-remote-image-render-py
        st.caption(f"Model used: {turn['model']} at {turn['timestamp']}")

for turn in st.session_state.chat_history:
    if turn.role == "user":
        with st.chat_message("user"):
            # ok: llm-markdown-remote-image-render-py
            st.markdown(turn.content)
    elif turn.role == "assistant":
        with st.chat_message("assistant"):
            # ruleid: llm-markdown-remote-image-render-py
            st.markdown(turn.content)

left, right = st.columns(2)
# ruleid: llm-markdown-remote-image-render-py
right.write(answer)
for column, metric in zip(st.columns(3), ["signups", "activations", "churn"]):
    # ruleid: llm-markdown-remote-image-render-py
    column.success(answer)
for tab in st.tabs(["Answer", "Sources"]):
    # ruleid: llm-markdown-remote-image-render-py
    tab.markdown(answer)

# Escaped text inside <pre> isn't parsed as Markdown; inside a <div> it is, after a blank line.
import html

# ok: llm-markdown-remote-image-render-py
st.markdown(f"<pre>{html.escape(answer)}</pre>", unsafe_allow_html=True)
# ruleid: llm-markdown-remote-image-render-py
st.markdown(f"<div class='note'>{html.escape(answer)}</div>", unsafe_allow_html=True)

# Images stripped first.
# ok: llm-markdown-remote-image-render-py
st.markdown(strip_images(answer))
# ok: llm-markdown-remote-image-render-py
st.markdown(re.sub(r"!\[[^\]]*\]\([^)]*\)", "", answer))
# ok: llm-markdown-remote-image-render-py
st.markdown(IMAGE_MARKDOWN.sub("", answer))

# Plain text, code, and metadata don't render Markdown images.
# ok: llm-markdown-remote-image-render-py
st.text(answer)
# ok: llm-markdown-remote-image-render-py
st.code(answer, language="markdown")
# ok: llm-markdown-remote-image-render-py
st.caption(f"{resp.usage.total_tokens} tokens, model {resp.model}")
# A length or count of the answer, inline, can't carry an image.
# ok: llm-markdown-remote-image-render-py
st.markdown(f"Answer length: {len(answer)} characters")
# ok: llm-markdown-remote-image-render-py
st.markdown("Lines: {}".format(len(answer.splitlines())))
# ok: llm-markdown-remote-image-render-py
st.markdown("Words: %d" % len(answer.split()))
# ok: llm-markdown-remote-image-render-py
st.caption(f"Score: {float(answer):.1f}")

# Not Streamlit: a log line and a file.
import logging

log = logging.getLogger(__name__)
# ok: llm-markdown-remote-image-render-py
log.info(answer)
with open("answers.md", "a") as fh:
    # ok: llm-markdown-remote-image-render-py
    fh.write(answer)

# Our own text.
# ok: llm-markdown-remote-image-render-py
st.markdown("![logo](https://example.com/logo.png) Growth dashboard")

# Values next to model output that the model didn't write.
import json

# pydantic-ai message parts: the user's prompt and our system prompt; the text part is the model's.
for message in st.session_state.messages:
    for part in message.parts:
        if part.part_kind == "system-prompt":
            # ok: llm-markdown-remote-image-render-py
            st.markdown(f"**System:** {part.content}")
        elif part.part_kind == "user-prompt":
            # ok: llm-markdown-remote-image-render-py
            st.markdown(part.content)
        elif part.part_kind == "text":
            # ruleid: llm-markdown-remote-image-render-py
            st.markdown(part.content)

for i, turn in enumerate(st.session_state.messages):
    # ok: llm-markdown-remote-image-render-py
    st.markdown(f"#### Turn {i + 1}")

for n, (question, reply) in enumerate(st.session_state.qa_history):
    # ok: llm-markdown-remote-image-render-py
    st.markdown(f"**Q{n + 1}:** {question}")
    # ruleid: llm-markdown-remote-image-render-py
    st.markdown(f"**A{n + 1}:** {reply}")
for pair in st.session_state.qa_history:
    with st.chat_message("user"):
        # ok: llm-markdown-remote-image-render-py
        st.write(pair[0])
    with st.chat_message("assistant"):
        # ruleid: llm-markdown-remote-image-render-py
        st.write(pair[1])

review = st.session_state.review_response
# Numeric format specs.
# ok: llm-markdown-remote-image-render-py
st.caption(f"Confidence: {review['confidence']:.0%}")
# ok: llm-markdown-remote-image-render-py
st.markdown(f"Average: {review['average']:.2f} / 5")
# ok: llm-markdown-remote-image-render-py
st.markdown("Average %.1f over %d answers" % (review["average"], review["count"]))
# ok: llm-markdown-remote-image-render-py
st.markdown("Average {:.1f}".format(review["average"]))
# A width or %s spec still takes a string.
# ruleid: llm-markdown-remote-image-render-py
st.markdown(f"Verdict: {review['verdict']:>12}")
# ruleid: llm-markdown-remote-image-render-py
st.markdown("Verdict: %s" % review["verdict"])
# A colon in a dict literal isn't a format spec.
# ruleid: llm-markdown-remote-image-render-py
st.markdown(json.dumps({"verdict": review["verdict"]}))

# Keys we wrote, and a score already divided by a number.
criteria = {
    "Clarity": review.get("clarity", 0),
    "Accuracy": review.get("accuracy", 0),
}
for label, points in criteria.items():
    # ok: llm-markdown-remote-image-render-py
    st.markdown(f"**{label}**")
    st.progress(points / 10)
    # ok: llm-markdown-remote-image-render-py
    st.markdown(f"{points} / 10")
for label, points in criteria.items():
    name_col, bar_col, value_col = st.columns([2, 3, 1])
    with bar_col:
        st.progress(points / 10)
    with value_col:
        # ok: llm-markdown-remote-image-render-py
        st.markdown(f"<b>{points}/10</b>", unsafe_allow_html=True)
for label, points in review.items():
    # The model wrote these keys.
    # ruleid: llm-markdown-remote-image-render-py
    st.markdown(f"**{label}**: {points}")

outcome = st.session_state.last_answer
# ok: llm-markdown-remote-image-render-py
st.error(f"Failed: {outcome.get('error', 'unknown error')}")
# ok: llm-markdown-remote-image-render-py
st.caption(outcome["created_at"])
# st.write shows a dict or list with st.json, not Markdown.
log_row = {"answer": outcome, "rating": "up"}
# ok: llm-markdown-remote-image-render-py
st.write("Saved:", log_row)
# ok: llm-markdown-remote-image-render-py
st.write([outcome, "up"])
# ruleid: llm-markdown-remote-image-render-py
st.write("Answer:", outcome)
# ruleid: llm-markdown-remote-image-render-py
st.markdown(log_row)

# A retrieved document's metadata.
docs = retriever.invoke(question)
for doc in docs:
    # ok: llm-markdown-remote-image-render-py
    st.write(f"Source: {doc.metadata['source']}")

# A game's move log isn't a chat history.
for move in st.session_state.move_history:
    # ok: llm-markdown-remote-image-render-py
    st.markdown(f"Move {move['number']} by {move['player']}")

# Labels we wrote, in the same tuples as the replies.
steps = [
    ("🔍", "Research", st.session_state.research_response),
    ("✍️", "Draft", st.session_state.get("draft_response")),
]
for icon, label, reply in steps:
    if reply:
        # ok: llm-markdown-remote-image-render-py
        st.success(f"{icon} {label} done")
        # ruleid: llm-markdown-remote-image-render-py
        st.markdown(reply)
for label, reply in [("Summary", st.session_state.summary_response), (title_for(st.session_state.chat_history), "")]:
    # A label the model may have written in one of the tuples.
    # ruleid: llm-markdown-remote-image-render-py
    st.markdown(f"### {label}")

CHART = re.compile(r"!\[([^\]]*)\]\((data:image/png;base64,[A-Za-z0-9+/=]+)\)")
pieces = CHART.split(st.session_state.report_response)
for n in range(1, len(pieces), 3):
    # ruleid: llm-markdown-remote-image-render-py
    st.markdown(f"![chart]({pieces[n + 1]})")


def answer_with_sources(question):
    reply = client.responses.create(model="gpt-5", input=question)
    return {"text": reply.output_text, "sources": [hit.payload["url"] for hit in search_docs(question)]}


answer = answer_with_sources(st.session_state.pending_question)
for url in answer["sources"]:
    # ok: llm-markdown-remote-image-render-py
    st.markdown(f"- {url}")
