import markdown
import mistune
from flask import Flask
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from openai import OpenAI

app = Flask(__name__)
client = OpenAI()

# Images turned off or rendered by our own code: markdown-it-py's image rule disabled,
# Python-Markdown's image patterns removed, and a mistune renderer with its own image().
md = MarkdownIt("commonmark")
md.disable(["image", "html_inline"])

converter = markdown.Markdown(extensions=["tables"])
converter.inlinePatterns.deregister("image_link")
converter.inlinePatterns.deregister("image_reference")


class LinkOnlyRenderer(mistune.HTMLRenderer):
    def image(self, text, url, title=None):
        return f'<a href="{mistune.escape(url)}">{text}</a>'


link_only = mistune.create_markdown(renderer=LinkOnlyRenderer())


@app.post("/preview")
def preview():
    resp = client.chat.completions.create(model="gpt-5", messages=[{"role": "user", "content": "hi"}])
    text = resp.choices[0].message.content
    # ok: llm-markdown-remote-image-render-py
    a = md.render(text)
    # ok: llm-markdown-remote-image-render-py
    b = converter.convert(text)
    # ok: llm-markdown-remote-image-render-py
    c = link_only(text)
    return a + b + c
