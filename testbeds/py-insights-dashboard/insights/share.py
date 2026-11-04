"""Gradio version of the dashboard for stakeholders without dashboard access.

Run with `python -m insights.share`.
"""

import gradio as gr

from insights import formatting, metrics
from insights.llm import (
    ANALYST_MODEL,
    REPORT_MODEL,
    analyst_messages,
    claude,
    openai_client,
)

kpis = metrics.load_kpis()

# The analyst formats answers with <b>, <ul>, and <table>, which the default sanitizer
# turns into escaped text inside tables, so the chat keeps the model's markup.
ANALYST_CHAT = gr.Chatbot(
    type="messages",
    height=520,
    sanitize_html=False,
    placeholder="Ask about signups, activations, or churn",
)


def ask_analyst(message, history):
    stream = openai_client.chat.completions.create(
        model=ANALYST_MODEL,
        messages=analyst_messages(history, message, metrics.kpi_table(kpis)),
        stream=True,
    )
    reply = ""
    for chunk in stream:
        if chunk.choices:
            reply += chunk.choices[0].delta.content or ""
            yield reply


def draft_notes(metric):
    message = claude.messages.create(
        model=REPORT_MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": f"Three bullet notes on {metric}:\n{metrics.kpi_table(kpis)}"}],
    )
    return message.content[0].text


def review_metric(metric):
    message = claude.messages.create(
        model=REPORT_MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": f"Is the {metric} trend healthy? One sentence."}],
    )
    return message.content[0].text, metrics.sparkline_svg(kpis, metric)


with gr.Blocks(title="Growth insights") as demo:
    with gr.Tab("Ask"):
        gr.ChatInterface(fn=ask_analyst, chatbot=ANALYST_CHAT, type="messages")

    with gr.Tab("Weekly summary"):
        metric_picker = gr.Dropdown(list(metrics.KPI_NAMES), value="signups", label="Metric")
        refresh = gr.Button("Summarize")
        summary = gr.HTML(label="Summary")

        @refresh.click(inputs=metric_picker, outputs=summary)
        def weekly_summary(metric):
            message = claude.messages.create(
                model=REPORT_MODEL,
                max_tokens=600,
                messages=[
                    {"role": "user", "content": f"Summarize {metric} this week in HTML.\n{metrics.kpi_table(kpis)}"}
                ],
            )
            return formatting.summary_card(metric, message.content[0].text)

    with gr.Tab("Notes"):
        notes = gr.Markdown()
        notes_btn = gr.Button("Draft notes")
        notes_btn.click(draft_notes, inputs=metric_picker, outputs=notes)

    with gr.Tab("Review"):
        verdict = gr.Textbox(label="Verdict")
        trend = gr.HTML()
        review = gr.Button("Review trend")
        review.click(review_metric, inputs=metric_picker, outputs=[verdict, trend])


if __name__ == "__main__":
    demo.launch()
