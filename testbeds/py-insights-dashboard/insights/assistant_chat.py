"""Chainlit chat for the analytics assistant, embedded in the team's intranet page.

Run with `chainlit run insights/assistant_chat.py`.
"""

import chainlit as cl
from openai import AsyncOpenAI

from insights import metrics
from insights.llm import ANALYST_MODEL, analyst_messages
from insights.markdown_safety import without_images

analyst = AsyncOpenAI()
kpis = metrics.load_kpis()


@cl.step(type="tool", name="Metric context")
async def metric_context(question: str):
    response = await analyst.responses.create(
        model=ANALYST_MODEL,
        input=f"Which KPIs does this question touch, and how did they move?\n{question}\n\n"
        f"{metrics.kpi_table(kpis)}",
    )
    return response.output_text


@cl.on_chat_start
async def start():
    cl.user_session.set("history", [])
    await cl.Message(content=f"KPIs loaded through week {kpis['week'].iloc[-1]}.").send()


@cl.on_message
async def on_message(message: cl.Message):
    history = cl.user_session.get("history")
    await metric_context(message.content)

    reply = cl.Message(content="")
    stream = await analyst.chat.completions.create(
        model=ANALYST_MODEL,
        messages=analyst_messages(history, message.content, metrics.kpi_table(kpis)),
        stream=True,
    )
    answer = ""
    async for chunk in stream:
        if chunk.choices and (token := chunk.choices[0].delta.content):
            answer += token
            await reply.stream_token(token)
    await reply.send()

    history.append({"role": "user", "content": message.content})
    history.append({"role": "assistant", "content": answer})

    if len(history) >= 6:
        recap = await analyst.responses.create(
            model=ANALYST_MODEL, input=f"Recap this conversation in three bullets:\n{history}"
        )
        await cl.Message(content=without_images(recap.output_text), author="Recap").send()
