from dash import Dash, Input, Output, dcc, html
from nicegui import ui
from openai import OpenAI

client = OpenAI()


def ask(question: str) -> str:
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    return resp.choices[0].message.content


# NiceGUI: ui.markdown sanitizes HTML in the browser but keeps images.
resp = client.chat.completions.create(model="gpt-5", messages=[{"role": "user", "content": "hi"}])
# ruleid: llm-markdown-remote-image-render-py
ui.markdown(resp.choices[0].message.content)
# ruleid: llm-markdown-remote-image-render-py
ui.markdown(content=resp.choices[0].message.content, extras=["tables"])
answer_box = ui.markdown("Thinking...")
# ruleid: llm-markdown-remote-image-render-py
answer_box.content = resp.choices[0].message.content
# ok: llm-markdown-remote-image-render-py
ui.label(resp.choices[0].message.content)
# ok: llm-markdown-remote-image-render-py
ui.markdown(f"**Model:** {resp.model}")


# Dash: dcc.Markdown renders images with no URL transform.
app = Dash(__name__)
app.layout = html.Div(
    [
        dcc.Input(id="question"),
        dcc.Markdown(id="answer"),
        html.Pre(id="raw"),
    ]
)


@app.callback(Output("answer", "children"), Input("question", "value"))
def answer(question):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    # ruleid: llm-markdown-remote-image-render-py
    return resp.choices[0].message.content


@app.callback(Output("raw", "children"), Input("question", "value"))
def raw(question):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    # ok: llm-markdown-remote-image-render-py
    return resp.choices[0].message.content


def card(question):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    # ruleid: llm-markdown-remote-image-render-py
    return html.Div([dcc.Markdown(children=resp.choices[0].message.content)])
