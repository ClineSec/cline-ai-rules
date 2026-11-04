import html

import panel as pn
from dash import Dash, Input, Output, State, dcc
from dash import html as dhtml
from IPython.display import HTML, display
from langchain_openai import ChatOpenAI
from nicegui import ui
from openai import OpenAI

client = OpenAI()
llm = ChatOpenAI(model="gpt-5")


# Panel: the HTML pane and Markdown render raw HTML.
def panel_report(question: str):
    resp = client.responses.create(model="gpt-5", input=question)
    # ruleid: llm-output-rendered-as-html
    report = pn.pane.HTML(resp.output_text)
    # ok: llm-output-rendered-as-html
    safe = pn.pane.HTML(resp.output_text, sanitize_html=True)
    # ruleid: llm-output-rendered-as-html
    notes = pn.pane.Markdown(object=resp.output_text)
    # ok: llm-output-rendered-as-html
    plain = pn.pane.Str(resp.output_text)
    return pn.Column(report, safe, notes, plain)


narrative = pn.pane.Markdown(sizing_mode="stretch_width")
sanitized = pn.pane.HTML(sanitize_html=True)


def panel_refresh(event):
    resp = client.responses.create(model="gpt-5", input=f"Explain {event.new}")
    # ruleid: llm-output-rendered-as-html
    narrative.object = resp.output_text
    # ok: llm-output-rendered-as-html
    sanitized.object = resp.output_text


def panel_callback(contents, user, instance):
    answer = llm.invoke(contents)
    # ruleid: llm-output-rendered-as-html
    return answer.content


chat = pn.chat.ChatInterface(callback=panel_callback)


def panel_streaming(contents, user, instance):
    message = None
    for chunk in llm.stream(contents):
        # ruleid: llm-output-rendered-as-html
        message = instance.stream(chunk.content, message=message)


def panel_echo(contents, user, instance):
    # ok: llm-output-rendered-as-html
    return f"You said: {html.escape(contents)}"


pn.chat.ChatInterface(callback=panel_echo)


# NiceGUI sanitizes with DOMPurify unless sanitize=False.
def nicegui_answer(question: str) -> None:
    text = llm.invoke(question).content
    # ruleid: llm-output-rendered-as-html
    ui.html(text, sanitize=False)
    # ok: llm-output-rendered-as-html
    ui.html(text)
    # ruleid: llm-output-rendered-as-html
    ui.chat_message(text, name="Assistant", text_html=True, sanitize=False)
    # ok: llm-output-rendered-as-html
    ui.chat_message(text, name="Assistant", text_html=True)
    live = ui.markdown(sanitize=False)
    # ruleid: llm-output-rendered-as-html
    live.content = text
    # ruleid: llm-output-rendered-as-html
    ui.add_body_html(f"<div id='banner'>{text}</div>")


# Dash: dcc.Markdown with dangerously_allow_html, and unsandboxed srcDoc frames.
app = Dash(__name__)
app.layout = dhtml.Div(
    [
        dcc.Input(id="question"),
        dcc.Markdown(id="answer", dangerously_allow_html=True),
        dcc.Markdown(id="summary"),
    ]
)


@app.callback(Output("answer", "children"), Input("question", "value"))
def dash_answer(question):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    # ruleid: llm-output-rendered-as-html
    return resp.choices[0].message.content


@app.callback(Output("summary", "children"), Input("question", "value"))
def dash_summary(question):
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    # ok: llm-output-rendered-as-html
    return resp.choices[0].message.content


def dash_preview(question):
    page = llm.invoke(question).content
    # ruleid: llm-output-rendered-as-html
    frame = dhtml.Iframe(srcDoc=page)
    # ok: llm-output-rendered-as-html
    boxed = dhtml.Iframe(srcDoc=page, sandbox="allow-scripts")
    # ruleid: llm-output-rendered-as-html
    card = dcc.Markdown(page, dangerously_allow_html=True)
    return [frame, boxed, card]


# Notebooks: HTML display objects run inline script.
def notebook_preview(question: str) -> None:
    resp = client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    # ruleid: llm-output-rendered-as-html
    display(HTML(resp.choices[0].message.content))
    # ok: llm-output-rendered-as-html
    display(HTML(f"<pre>{html.escape(resp.choices[0].message.content)}</pre>"))
