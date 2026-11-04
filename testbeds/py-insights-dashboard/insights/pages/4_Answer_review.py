"""Answer review: replay this session's analyst answers and grade the latest one."""

import json

import streamlit as st

from insights.llm import REPORT_MODEL, openai_client

GRADING_PROMPT = (
    "Grade the analytics answer below for a growth team. Reply with JSON only: accuracy, "
    "clarity and actionability as integers from 0 to 5, confidence from 0 to 1, and a "
    "one-paragraph verdict."
)

st.title("Answer review")

if not st.session_state.get("chat_history"):
    st.info("Ask the analyst something on the home page first.")
    st.stop()

for number, turn in enumerate(st.session_state.chat_history, start=1):
    if turn["role"] == "user":
        with st.chat_message("user"):
            st.markdown(f"**Question {number}:** {turn['content']}")
        continue
    with st.chat_message("assistant"):
        st.markdown(turn["content"])
        st.caption(f"Turn {number} · {turn.get('model', 'unknown model')} · {turn.get('timestamp', '')}")

review_steps = [
    ("📝", "Answer to review", st.session_state.chat_history[-1]["content"]),
    ("✅", "Graded", st.session_state.get("grade_response")),
]
for icon, step, value in review_steps:
    if value:
        st.sidebar.markdown(f"{icon} {step}")

if st.button("Grade the latest answer"):
    latest = st.session_state.chat_history[-1]["content"]
    grading = openai_client.chat.completions.create(
        model=REPORT_MODEL,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": f"{GRADING_PROMPT}\n\n{latest}"}],
    )
    grades = json.loads(grading.choices[0].message.content)
    rubric = {
        "Accuracy": grades.get("accuracy", 0),
        "Clarity": grades.get("clarity", 0),
        "Actionability": grades.get("actionability", 0),
    }
    for criterion, score in rubric.items():
        label_col, bar_col, value_col = st.columns([2, 3, 1])
        label_col.markdown(f"**{criterion}**")
        with bar_col:
            st.progress(score / 5)
        with value_col:
            st.markdown(f"**{score}/5**")
    st.caption(f"Grader confidence: {grades.get('confidence', 0):.0%}")
    st.info(grades.get("verdict", "No verdict returned."))
