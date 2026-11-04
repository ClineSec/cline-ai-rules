import html

import jinja2
import markdown
import mistune
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from openai import AsyncOpenAI

app = FastAPI()
client = AsyncOpenAI()
templates = Jinja2Templates(directory="templates")
mail_env = jinja2.Environment(loader=jinja2.FileSystemLoader("mail"))
safe_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("mail"), autoescape=jinja2.select_autoescape()
)


async def draft(question: str) -> str:
    resp = await client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    return resp.choices[0].message.content


@app.get("/answer")
async def answer(q: str):
    resp = await client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": q}]
    )
    text = resp.choices[0].message.content
    # ruleid: llm-output-rendered-as-html
    return HTMLResponse(f"<article>{text}</article>")


@app.get("/answer.md")
async def answer_markdown(q: str):
    resp = await client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": q}]
    )
    # Python-Markdown passes raw HTML through.
    # ruleid: llm-output-rendered-as-html
    return HTMLResponse(content=markdown.markdown(resp.choices[0].message.content))


@app.get("/answer-escaped")
async def answer_escaped(q: str):
    resp = await client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": q}]
    )
    # ok: llm-output-rendered-as-html
    return HTMLResponse(mistune.markdown(resp.choices[0].message.content))


@app.get("/answer.txt")
async def answer_text(q: str):
    resp = await client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": q}]
    )
    # ok: llm-output-rendered-as-html
    return PlainTextResponse(resp.choices[0].message.content)


@app.get("/answer.json")
async def answer_json(q: str):
    resp = await client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": q}]
    )
    # ok: llm-output-rendered-as-html
    return resp.choices[0].message.content


@app.get("/fragment", response_class=HTMLResponse)
async def fragment(q: str):
    resp = await client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": q}]
    )
    # ruleid: llm-output-rendered-as-html
    return f"<section>{resp.choices[0].message.content}</section>"


@app.get("/raw")
async def raw(q: str):
    resp = await client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": q}]
    )
    # ruleid: llm-output-rendered-as-html
    return Response(resp.choices[0].message.content, media_type="text/html")


@app.get("/page")
async def page(request: Request, q: str):
    resp = await client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": q}]
    )
    text = resp.choices[0].message.content
    # ok: llm-output-rendered-as-html
    plain = templates.TemplateResponse(request, "answer.html", {"answer": text})
    # ruleid: llm-output-rendered-as-html
    trusted = templates.TemplateResponse(request, "answer.html", {"answer": Markup(text)})
    return plain if q else trusted


@app.get("/digest", response_class=HTMLResponse)
async def digest(q: str):
    resp = await client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": q}]
    )
    text = resp.choices[0].message.content
    # ruleid: llm-output-rendered-as-html
    body = mail_env.get_template("digest.html").render(summary=text)
    # ok: llm-output-rendered-as-html
    note = mail_env.get_template("digest.txt").render(summary=text)
    # ok: llm-output-rendered-as-html
    safe = safe_env.get_template("digest.html").render(summary=text)
    # ok: llm-output-rendered-as-html
    return body + note + safe


@app.get("/card")
async def card(q: str):
    text = await draft(q)
    # ok: llm-output-rendered-as-html
    return HTMLResponse(Markup("<div class='card'>{}</div>").format(text))


@app.get("/card-escaped")
async def card_escaped(q: str):
    resp = await client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": q}]
    )
    # ok: llm-output-rendered-as-html
    return HTMLResponse(f"<p>{html.escape(resp.choices[0].message.content)}</p>")
