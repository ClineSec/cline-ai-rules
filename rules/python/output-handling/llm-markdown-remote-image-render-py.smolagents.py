import streamlit as st
from smolagents import CodeAgent, InferenceClientModel, ToolCallingAgent, WebSearchTool

model = InferenceClientModel()
researcher = ToolCallingAgent(tools=[WebSearchTool()], model=model)
coder = CodeAgent(tools=[], model=model, managed_agents=[researcher])

if prompt := st.chat_input("Ask the research desk"):
    with st.chat_message("assistant"):
        answer = coder.run(prompt, reset=False)
        # ruleid: llm-markdown-remote-image-render-py
        st.markdown(answer)
    # ruleid: llm-markdown-remote-image-render-py
    st.sidebar.markdown(str(researcher.run(f"Sources for: {prompt}")))
