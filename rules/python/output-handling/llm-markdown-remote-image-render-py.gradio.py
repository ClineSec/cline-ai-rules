import re

import gradio as gr
import litellm
from openai import OpenAI

client = OpenAI()


def without_images(text: str) -> str:
    return re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)


def chat(message, history):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[*history, {"role": "user", "content": message}]
    )
    # ruleid: llm-markdown-remote-image-render-py
    return resp.choices[0].message.content


# The default Chatbot sanitizes HTML but keeps images.
chat_ui = gr.ChatInterface(chat)


def chat_stream(message, history):
    stream = litellm.completion(
        model="gpt-5", messages=[*history, {"role": "user", "content": message}], stream=True
    )
    partial = ""
    for chunk in stream:
        partial += chunk.choices[0].delta.content or ""
        # ruleid: llm-markdown-remote-image-render-py
        yield partial


stream_ui = gr.ChatInterface(fn=chat_stream, chatbot=gr.Chatbot(render_markdown=False))


def chat_safe(message, history):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[*history, {"role": "user", "content": message}]
    )
    # ok: llm-markdown-remote-image-render-py
    return without_images(resp.choices[0].message.content)


safe_ui = gr.ChatInterface(chat_safe)


def summarize(text):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": f"Summarize: {text}"}]
    )
    # ruleid: llm-markdown-remote-image-render-py
    return resp.choices[0].message.content


def summarize_text(text):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": f"Summarize: {text}"}]
    )
    # ok: llm-markdown-remote-image-render-py
    return resp.choices[0].message.content


md_summary = gr.Interface(summarize, "text", "markdown")
text_summary = gr.Interface(fn=summarize_text, inputs="text", outputs="text")


def respond(message, history):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[*history, {"role": "user", "content": message}]
    )
    history.append({"role": "assistant", "content": resp.choices[0].message.content})
    # ruleid: llm-markdown-remote-image-render-py
    return "", history


def explain(question):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    answer = resp.choices[0].message.content
    # ruleid: llm-markdown-remote-image-render-py
    return answer, f"{resp.usage.total_tokens} tokens"


def verdict(question):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    # ok: llm-markdown-remote-image-render-py
    return resp.choices[0].message.content, resp.usage.total_tokens


with gr.Blocks() as demo:
    chatbot = gr.Chatbot(type="messages")
    msg = gr.Textbox()
    msg.submit(respond, [msg, chatbot], [msg, chatbot])

    question = gr.Textbox()
    explanation = gr.Markdown()
    usage = gr.Markdown()
    gr.Button("Explain").click(explain, inputs=question, outputs=[explanation, usage])

    plain = gr.Textbox()
    count = gr.Number()
    gr.Button("Verdict").click(verdict, inputs=question, outputs=[plain, count])

    notes = gr.Markdown()

    @gr.on(triggers=[question.submit], inputs=question, outputs=notes)
    def draft_notes(q):
        resp = client.chat.completions.create(
            model="gpt-5", messages=[{"role": "user", "content": q}]
        )
        # ruleid: llm-markdown-remote-image-render-py
        return resp.choices[0].message.content

    resp = client.chat.completions.create(model="gpt-5", messages=[{"role": "user", "content": "hi"}])
    # ruleid: llm-markdown-remote-image-render-py
    gr.Markdown(resp.choices[0].message.content)
    # ruleid: llm-markdown-remote-image-render-py
    gr.Chatbot(value=[{"role": "assistant", "content": resp.choices[0].message.content}])
    # ok: llm-markdown-remote-image-render-py
    gr.Textbox(value=resp.choices[0].message.content)
    # ok: llm-markdown-remote-image-render-py
    gr.Markdown(f"Model: {resp.model}")
