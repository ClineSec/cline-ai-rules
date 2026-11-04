import html

import gradio as gr
import litellm
from openai import OpenAI

client = OpenAI()


def summarize(text: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": f"Summarize as HTML: {text}"}]
    )
    # ruleid: llm-output-rendered-as-html
    return resp.choices[0].message.content


def summarize_plain(text: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": f"Summarize: {text}"}]
    )
    # ok: llm-output-rendered-as-html
    return resp.choices[0].message.content


def summarize_escaped(text: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": f"Summarize: {text}"}]
    )
    # ok: llm-output-rendered-as-html
    return "<pre>" + html.escape(resp.choices[0].message.content) + "</pre>"


html_summary = gr.Interface(summarize, "text", "html")
plain_summary = gr.Interface(fn=summarize_plain, inputs="text", outputs="markdown")
escaped_summary = gr.Interface(summarize_escaped, "text", gr.HTML())


def chat(message, history):
    stream = litellm.completion(
        model="gpt-5", messages=[*history, {"role": "user", "content": message}], stream=True
    )
    partial = ""
    for chunk in stream:
        partial += chunk.choices[0].delta.content or ""
        # ruleid: llm-output-rendered-as-html
        yield partial


chat_ui = gr.ChatInterface(chat, chatbot=gr.Chatbot(sanitize_html=False))


def chat_safe(message, history):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[*history, {"role": "user", "content": message}]
    )
    # ok: llm-output-rendered-as-html
    return resp.choices[0].message.content


safe_chat_ui = gr.ChatInterface(chat_safe, chatbot=gr.Chatbot())


def respond(message, history):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[*history, {"role": "user", "content": message}]
    )
    history.append({"role": "assistant", "content": resp.choices[0].message.content})
    # ruleid: llm-output-rendered-as-html
    return "", history


def explain(question):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    answer = resp.choices[0].message.content
    # ruleid: llm-output-rendered-as-html
    return answer, f"{resp.usage.total_tokens} tokens"


def explain_text(question):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    # ok: llm-output-rendered-as-html
    return resp.choices[0].message.content, "<b>done</b>"


with gr.Blocks() as demo:
    msg = gr.Textbox()
    chatbot = gr.Chatbot(type="messages", sanitize_html=False)
    msg.submit(respond, [msg, chatbot], [msg, chatbot])

    question = gr.Textbox()
    rendered = gr.HTML()
    usage = gr.Textbox()
    with gr.Row():
        ask_btn = gr.Button("Ask")
        text_btn = gr.Button("Ask (text)")
    ask_btn.click(explain, inputs=question, outputs=[rendered, usage])
    text_btn.click(explain_text, inputs=question, outputs=[usage, rendered])

    @ask_btn.click(inputs=question, outputs=gr.HTML())
    def card(q):
        resp = client.chat.completions.create(
            model="gpt-5", messages=[{"role": "user", "content": q}]
        )
        # ruleid: llm-output-rendered-as-html
        return f"<div class='card'>{resp.choices[0].message.content}</div>"

    def badge(q):
        resp = client.chat.completions.create(
            model="gpt-5", messages=[{"role": "user", "content": q}]
        )
        # ruleid: llm-output-rendered-as-html
        return gr.HTML(value=resp.choices[0].message.content)

    ask_btn.click(badge, question, gr.Textbox())

    def note(q):
        resp = client.chat.completions.create(
            model="gpt-5", messages=[{"role": "user", "content": q}]
        )
        # ok: llm-output-rendered-as-html
        return gr.Markdown(value=resp.choices[0].message.content)

    text_btn.click(note, question, gr.Textbox())

    # Outputs written in parentheses: a component picked by a setting. These made OpenGrep
    # 1.30.2 abort the whole file; they count like the bare forms.
    rich_answers = True
    html_answer = gr.HTML()
    text_answer = gr.Textbox()

    def brief(q):
        resp = client.chat.completions.create(
            model="gpt-5", messages=[{"role": "user", "content": f"Brief me on {q}"}]
        )
        # ruleid: llm-output-rendered-as-html
        return resp.choices[0].message.content

    ask_btn.click(brief, inputs=question, outputs=(gr.HTML(label="Brief") if rich_answers else gr.Textbox()))

    def digest(q):
        resp = client.chat.completions.create(
            model="gpt-5", messages=[{"role": "user", "content": f"Digest: {q}"}]
        )
        # ruleid: llm-output-rendered-as-html
        return resp.choices[0].message.content

    text_btn.click(digest, inputs=question, outputs=(html_answer if rich_answers else text_answer))

    # A tuple of outputs: the HTML box gets a fixed label and the model text goes to a textbox.
    def labelled(q):
        resp = client.chat.completions.create(
            model="gpt-5", messages=[{"role": "user", "content": q}]
        )
        # ok: llm-output-rendered-as-html
        return "<b>Answer</b>", resp.choices[0].message.content

    text_btn.click(labelled, question, (html_answer, text_answer))
