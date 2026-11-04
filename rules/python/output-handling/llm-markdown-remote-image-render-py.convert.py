import smtplib
from email.message import EmailMessage

import bleach
import markdown
import mistune
import nh3
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from markdown_it import MarkdownIt
from openai import OpenAI

app = FastAPI()
client = OpenAI()
md = MarkdownIt("js-default")
zero = MarkdownIt("zero")
render = mistune.create_markdown(plugins=["table"])
ast = mistune.create_markdown(renderer="ast")
SUMMARY_TAGS = {"p", "ul", "ol", "li", "strong", "em", "code", "pre", "a"}


@app.get("/summary", response_class=HTMLResponse)
def summary(q: str):
    resp = client.chat.completions.create(model="gpt-5", messages=[{"role": "user", "content": q}])
    text = resp.choices[0].message.content
    # ruleid: llm-markdown-remote-image-render-py
    body = markdown.markdown(text, extensions=["tables"])
    # ruleid: llm-markdown-remote-image-render-py
    preview = md.render(text)
    # ruleid: llm-markdown-remote-image-render-py
    escaped = mistune.markdown(text)
    # ruleid: llm-markdown-remote-image-render-py
    plain = mistune.html(text)
    # ruleid: llm-markdown-remote-image-render-py
    tabled = render(text)
    # ruleid: llm-markdown-remote-image-render-py
    chained = MarkdownIt("commonmark").enable("table").render(text)
    # ruleid: llm-markdown-remote-image-render-py
    converted = markdown.Markdown(extensions=["toc"]).convert(text)
    # nh3's default tags keep img.
    # ruleid: llm-markdown-remote-image-render-py
    cleaned = nh3.clean(markdown.markdown(text))
    # ruleid: llm-markdown-remote-image-render-py
    with_img = bleach.clean(markdown.markdown(text), tags={"p", "a", "img"}, attributes={"img": ["src"]})
    return "".join([body, preview, escaped, plain, tabled, chained, converted, cleaned, with_img])


@app.get("/summary-safe", response_class=HTMLResponse)
def summary_safe(q: str):
    resp = client.chat.completions.create(model="gpt-5", messages=[{"role": "user", "content": q}])
    text = resp.choices[0].message.content
    # ok: llm-markdown-remote-image-render-py
    a = bleach.clean(markdown.markdown(text))
    # ok: llm-markdown-remote-image-render-py
    b = nh3.clean(md.render(text), tags=SUMMARY_TAGS)
    # ok: llm-markdown-remote-image-render-py
    html_body = markdown.markdown(text)
    cleaned = bleach.clean(html_body, tags=["p", "ul", "li", "a"])
    # ok: llm-markdown-remote-image-render-py
    c = zero.render(text)
    # ok: llm-markdown-remote-image-render-py
    d = ast(text)
    # ok: llm-markdown-remote-image-render-py
    e = mistune.markdown(text, renderer="ast")
    # ok: llm-markdown-remote-image-render-py
    f = nh3.clean(markdown.markdown(text), tags=nh3.ALLOWED_TAGS - {"img"})
    # ok: llm-markdown-remote-image-render-py
    g = markdown.markdown("![logo](https://example.com/logo.png) Weekly summary")
    return "".join([a, b, cleaned, c, str(d), str(e), f, g])


def send_digest(to: str, tickets: list[str]) -> None:
    resp = client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": "Summarize in Markdown:\n" + "\n".join(tickets)}],
    )
    reply = resp.choices[0].message.content
    msg = EmailMessage()
    msg["To"] = to
    msg.set_content(reply)
    # ruleid: llm-markdown-remote-image-render-py
    msg.add_alternative(markdown.markdown(reply), subtype="html")
    with smtplib.SMTP("smtp.example.invalid") as smtp:
        smtp.send_message(msg)
