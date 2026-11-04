import asyncio
import subprocess

import requests

import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools

scout = Agent(
    name="Scout",
    model=OpenAIChat(id="gpt-5"),
    tools=[DuckDuckGoTools()],
    instructions="Find recent coverage of the topic and cite sources.",
    markdown=True,
)
desk = Team(name="News desk", members=[scout], model=OpenAIChat(id="gpt-5"))

topic = st.text_input("Topic")
if topic:
    run = scout.run(f"What changed this week in {topic}?")
    # ruleid: llm-markdown-remote-image-render-py
    st.markdown(run.content)
    # ruleid: llm-markdown-remote-image-render-py
    st.write(scout.run(f"One-line summary of {topic}").content)

    brief = asyncio.run(desk.arun(f"Write a brief on {topic}"))
    with st.expander("Brief"):
        # ruleid: llm-markdown-remote-image-render-py
        st.info(brief.content)

    box = st.empty()
    text = ""
    for event in scout.run(topic, stream=True):
        text += event.content or ""
        # ruleid: llm-markdown-remote-image-render-py
        box.markdown(text)

    # Shown as plain text, or only its length.
    # ok: llm-markdown-remote-image-render-py
    st.text(run.content)
    # ok: llm-markdown-remote-image-render-py
    st.caption(f"{len(run.content)} characters")

# A subprocess in the same app isn't model output.
build = subprocess.run(["git", "log", "-1", "--oneline"], capture_output=True, text=True)
# ok: llm-markdown-remote-image-render-py
st.markdown(f"Build: `{build.stdout}`")

# The router agent's pick, checked against the desks we run before it is shown.
DESKS = {"markets": "Markets desk", "tech": "Tech desk"}
pick = scout.run("Which desk covers this topic? Answer markets or tech.").content.strip()
if pick in DESKS:
    # ok: llm-markdown-remote-image-render-py
    st.success(f"Routed to {pick}")
    # ok: llm-markdown-remote-image-render-py
    st.caption(DESKS[pick])
else:
    # ruleid: llm-markdown-remote-image-render-py
    st.warning(f"No desk called {pick}")
if pick in ("markets", "tech"):
    # ok: llm-markdown-remote-image-render-py
    st.info(f"Desk: {pick}")
# A check against a list the model wrote isn't an allowlist.
if pick in run.content:
    # ruleid: llm-markdown-remote-image-render-py
    st.info(f"Desk: {pick}")

# The run's search citations and generated audio come from tools, not the model's text, and
# neither does the status of the download.
for source in run.citations.urls or []:
    # ok: llm-markdown-remote-image-render-py
    st.markdown(f"- [{source.title}]({source.url})")
clip = scout.run("Read the brief aloud.")
download = requests.get(clip.audio[0].url, timeout=10)
if not download.ok:
    # ok: llm-markdown-remote-image-render-py
    st.error(f"Download failed with status {download.status_code}")
    # ok: llm-markdown-remote-image-render-py
    st.write("Type:", download.headers.get("Content-Type"))
    # ok: llm-markdown-remote-image-render-py
    st.write("Audio link:", clip.audio[0].url)
# ruleid: llm-markdown-remote-image-render-py
st.markdown(clip.content)
