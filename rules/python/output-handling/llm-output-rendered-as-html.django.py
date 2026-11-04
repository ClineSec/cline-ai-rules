from anthropic import Anthropic
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.html import format_html
from django.utils.safestring import mark_safe

claude = Anthropic()


def ask(question: str) -> str:
    msg = claude.messages.create(
        model="claude-sonnet-5-5", max_tokens=600, messages=[{"role": "user", "content": question}]
    )
    return msg.content[0].text


def answer_view(request):
    msg = claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=600,
        messages=[{"role": "user", "content": request.GET["q"]}],
    )
    text = msg.content[0].text
    # ruleid: llm-output-rendered-as-html
    page = HttpResponse(f"<main>{text}</main>")
    # ok: llm-output-rendered-as-html
    plain = HttpResponse(text, content_type="text/plain; charset=utf-8")
    # ok: llm-output-rendered-as-html
    data = JsonResponse({"answer": text})
    return page or plain or data


def answer_page(request):
    msg = claude.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=600,
        messages=[{"role": "user", "content": request.GET["q"]}],
    )
    text = msg.content[0].text
    # ruleid: llm-output-rendered-as-html
    trusted = mark_safe(text)
    # ruleid: llm-output-rendered-as-html
    banner = format_html(text)
    # ok: llm-output-rendered-as-html
    card = format_html("<div class='card'>{}</div>", text)
    # ok: llm-output-rendered-as-html
    return render(request, "answer.html", {"answer": text, "trusted": trusted, "banner": banner, "card": card})
