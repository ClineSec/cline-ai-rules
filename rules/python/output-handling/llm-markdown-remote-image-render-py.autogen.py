import streamlit as st
from autogen import ConversableAgent, LLMConfig
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

llm_config = LLMConfig(api_type="openai", model="gpt-5")
reviewer = ConversableAgent("reviewer", llm_config=llm_config, system_message="Review the draft.")
author = ConversableAgent("author", llm_config=llm_config, human_input_mode="NEVER")

draft = st.text_area("Draft")
if st.button("Review") and draft:
    chat = author.initiate_chat(
        reviewer, message=draft, max_turns=2, summary_method="reflection_with_llm"
    )
    # ruleid: llm-markdown-remote-image-render-py
    st.markdown(chat.summary)
    for entry in chat.chat_history:
        # ruleid: llm-markdown-remote-image-render-py
        st.markdown(entry["content"])
    # ok: llm-markdown-remote-image-render-py
    st.caption(f"{len(chat.chat_history)} messages")


async def triage(ticket: str):
    helper = AssistantAgent("helper", model_client=OpenAIChatCompletionClient(model="gpt-5"))
    outcome = await helper.run(task=f"Triage this ticket: {ticket}")
    # ruleid: llm-markdown-remote-image-render-py
    st.markdown(outcome.messages[-1].content)
