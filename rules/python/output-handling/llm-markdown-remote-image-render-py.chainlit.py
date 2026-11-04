import chainlit as cl
from openai import AsyncOpenAI

client = AsyncOpenAI()
IMAGE_PATTERN = r"!\[[^\]]*\]\([^)]*\)"


def strip_markdown_images(text: str) -> str:
    import re

    return re.sub(IMAGE_PATTERN, "", text)


@cl.step(type="tool")
async def research(topic: str):
    resp = await client.responses.create(model="gpt-5", input=f"Research {topic}")
    # ruleid: llm-markdown-remote-image-render-py
    return resp.output_text


@cl.step
async def outline(topic: str):
    resp = await client.responses.create(model="gpt-5", input=f"Outline {topic}")
    # ok: llm-markdown-remote-image-render-py
    return strip_markdown_images(resp.output_text)


@cl.on_message
async def on_message(message: cl.Message):
    resp = await client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": message.content}]
    )
    answer = resp.choices[0].message.content
    # ruleid: llm-markdown-remote-image-render-py
    await cl.Message(content=answer).send()
    # ruleid: llm-markdown-remote-image-render-py
    await cl.Message(answer, author="Analyst").send()
    # ruleid: llm-markdown-remote-image-render-py
    await cl.ErrorMessage(content=f"Could not finish: {answer}").send()

    reply = cl.Message(content="")
    stream = await client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": message.content}], stream=True
    )
    async for chunk in stream:
        if token := chunk.choices[0].delta.content:
            # ruleid: llm-markdown-remote-image-render-py
            await reply.stream_token(token)
    await reply.send()

    summary = cl.Message(content="Summarizing...")
    await summary.send()
    # ruleid: llm-markdown-remote-image-render-py
    summary.content = answer
    await summary.update()

    async with cl.Step(name="critique") as step:
        critique = await client.responses.create(model="gpt-5", input=f"Critique: {answer}")
        # ruleid: llm-markdown-remote-image-render-py
        step.output = critique.output_text

    # ok: llm-markdown-remote-image-render-py
    await cl.Message(content=strip_markdown_images(answer)).send()
    # ok: llm-markdown-remote-image-render-py
    await cl.Message(content=f"Used {resp.usage.total_tokens} tokens").send()
    # ok: llm-markdown-remote-image-render-py
    await cl.Message(content="![status](https://example.com/ok.png) Done").send()
