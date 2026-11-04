# The agents are built in another module, so no framework import here: an agent, crew, or team
# by name is enough.
import asyncio

import streamlit as st

from desk.agents import planner_agent, research_crew, review_team, scheduler

goal = st.text_input("Goal")
if goal:
    # ruleid: llm-markdown-remote-image-render-py
    st.markdown(planner_agent.run(goal))
    # ruleid: llm-markdown-remote-image-render-py
    st.markdown(research_crew.kickoff(inputs={"goal": goal}).raw)
    review = asyncio.run(review_team.arun(goal))
    # ruleid: llm-markdown-remote-image-render-py
    st.write(review.content)
    # ruleid: llm-markdown-remote-image-render-py
    st.markdown(st.session_state.agent.run(goal))

    # A job scheduler's run isn't an agent's, and asyncio.run of our own coroutine isn't either.
    # ok: llm-markdown-remote-image-render-py
    st.markdown(scheduler.run(job="nightly-report"))
    # ok: llm-markdown-remote-image-render-py
    st.markdown(asyncio.run(load_greeting()))
