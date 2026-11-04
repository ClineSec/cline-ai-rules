import streamlit as st
from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

billing = Agent("openai:gpt-5", instructions="Answer billing questions for the customer.")


def show_part(part):
    if part.part_kind == "user-prompt":
        with st.chat_message("user"):
            # ok: llm-markdown-remote-image-render-py
            st.markdown(part.content)
    elif part.part_kind == "text":
        with st.chat_message("assistant"):
            # ruleid: llm-markdown-remote-image-render-py
            st.markdown(part.content)
    else:
        # ok: llm-markdown-remote-image-render-py
        st.caption(part.part_kind)


def show_response(message: ModelResponse):
    for part in message.parts:
        if isinstance(part, TextPart):
            # ruleid: llm-markdown-remote-image-render-py
            st.markdown(part.content)


for message in st.session_state.messages:
    for part in message.parts:
        if isinstance(part, UserPromptPart):
            # ok: llm-markdown-remote-image-render-py
            st.markdown(part.content)
        else:
            # ruleid: llm-markdown-remote-image-render-py
            st.markdown(part.content)


async def stream_answer(question: str):
    async with billing.run_stream(question, message_history=st.session_state.history) as result:
        async for delta in result.stream_text(delta=True):
            yield delta


async def main():
    question = st.chat_input("Ask about your bill")
    if not question:
        return

    result = await billing.run(question)
    # ruleid: llm-markdown-remote-image-render-py
    st.markdown(result.output)
    # ruleid: llm-markdown-remote-image-render-py
    st.write(billing.run_sync(question).output)

    with st.chat_message("assistant"):
        box = st.empty()
        text = ""
        async for delta in stream_answer(question):
            text += delta
            # ruleid: llm-markdown-remote-image-render-py
            box.markdown(text + "▌")

    live = st.empty()
    async with billing.run_stream(question) as streamed:
        async for so_far in streamed.stream_text():
            # ruleid: llm-markdown-remote-image-render-py
            live.markdown(so_far)

    # ok: llm-markdown-remote-image-render-py
    st.caption(f"{result.usage().total_tokens} tokens")
