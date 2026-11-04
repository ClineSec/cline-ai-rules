"""Writes the weekly report to a Markdown file and an HTML archive copy on disk."""

import pathlib

import markdown
from openai import OpenAI

client = OpenAI()

resp = client.responses.create(model="gpt-5", input="Write the weekly report in Markdown.")
report = resp.output_text
pathlib.Path("report.md").write_text(report)
# Not served, emailed, or shown in a UI from this file.
# ok: llm-markdown-remote-image-render-py
pathlib.Path("report.html").write_text(markdown.markdown(report))
