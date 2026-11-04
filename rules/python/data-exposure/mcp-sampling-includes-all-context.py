import functools
from dataclasses import dataclass
from typing import Annotated

import mcp.types as types
from mcp.server.mcpserver import Context, MCPServer, Resolve, Sample
from mcp.types import CreateMessageResult, IncludeContext, SamplingMessage, TextContent

mcp = MCPServer("review")

WIDE_CONTEXT = "allServers"
OWN_CONTEXT = "thisServer"


def _user(text: str) -> list[SamplingMessage]:
    return [SamplingMessage(role="user", content=TextContent(text=text))]


@mcp.tool()
async def explain_failure(log: str, ctx: Context) -> str:
    result = await ctx.session.create_message(
        messages=_user(f"Why did this build fail?\n\n{log}"),
        max_tokens=400,
        # ruleid: mcp-sampling-includes-all-context
        include_context="allServers",
    )
    return result.content.text


@mcp.tool()
async def review_diff(diff: str, ctx: Context) -> str:
    # ruleid: mcp-sampling-includes-all-context
    result = await ctx.session.create_message(messages=_user(diff), max_tokens=600, include_context=WIDE_CONTEXT)
    return result.content.text


def ask_for_summary(text: str) -> Sample:
    # ruleid: mcp-sampling-includes-all-context
    return Sample(_user(f"Summarize:\n{text}"), max_tokens=200, include_context="allServers")


@mcp.tool()
async def summarize(text: str, summary: Annotated[CreateMessageResult, Resolve(ask_for_summary)]) -> str:
    return summary.content.text


async def legacy_request(session, text: str):
    params = types.CreateMessageRequestParams(
        messages=_user(text),
        maxTokens=300,
        # ruleid: mcp-sampling-includes-all-context
        includeContext="allServers",
    )
    return await session.send_request(
        types.ServerRequest(types.CreateMessageRequest(method="sampling/createMessage", params=params)),
        types.CreateMessageResult,
    )


SAMPLING_DEFAULTS = {
    "max_tokens": 500,
    # ruleid: mcp-sampling-includes-all-context
    "include_context": "allServers",
}


async def ask(ctx: Context, text: str):
    return await ctx.session.create_message(messages=_user(text), **SAMPLING_DEFAULTS)


raw_params = {
    "messages": [{"role": "user", "content": {"type": "text", "text": "hi"}}],
    "maxTokens": 100,
    # ruleid: mcp-sampling-includes-all-context
    "includeContext": "allServers",
}


async def ask_client(
    ctx: Context,
    text: str,
    # ruleid: mcp-sampling-includes-all-context
    include_context: IncludeContext = "allServers",
):
    return await ctx.session.create_message(messages=_user(text), max_tokens=300, include_context=include_context)


@dataclass
class SamplingSettings:
    max_tokens: int = 400
    # ruleid: mcp-sampling-includes-all-context
    include_context: IncludeContext = "allServers"


def make_asker(ctx: Context):
    # ruleid: mcp-sampling-includes-all-context
    return functools.partial(ctx.session.create_message, max_tokens=200, include_context="allServers")


async def fastmcp2_tool(ctx, text: str, wide: bool) -> str:
    # fastmcp 2.10.6 to 2.14.0: Context.sample(..., include_context=...)
    # ruleid: mcp-sampling-includes-all-context
    reply = await ctx.sample(text, include_context="allServers" if wide else "none")
    return reply.text


async def late_flag(ctx: Context, text: str, wide: bool):
    kwargs = {"messages": _user(text), "max_tokens": 100}
    if wide:
        # ruleid: mcp-sampling-includes-all-context
        kwargs["include_context"] = "allServers"
    return await ctx.session.create_message(**kwargs)


def widen(params: types.CreateMessageRequestParams) -> types.CreateMessageRequestParams:
    # ruleid: mcp-sampling-includes-all-context
    params.include_context = WIDE_CONTEXT
    return params


# --- near misses ---


@mcp.tool()
async def explain_failure_scoped(log: str, ctx: Context) -> str:
    result = await ctx.session.create_message(
        messages=_user(f"Why did this build fail?\n\n{log}"),
        max_tokens=400,
        # ok: mcp-sampling-includes-all-context
        include_context="none",
    )
    return result.content.text


async def own_context(ctx: Context, text: str):
    # Context from the requesting server only: no other server's data.
    # ok: mcp-sampling-includes-all-context
    return await ctx.session.create_message(messages=_user(text), max_tokens=100, include_context="thisServer")


async def own_context_constant(ctx: Context, text: str):
    # ok: mcp-sampling-includes-all-context
    return await ctx.session.create_message(messages=_user(text), max_tokens=100, include_context=OWN_CONTEXT)


async def no_context(ctx: Context, text: str):
    # ok: mcp-sampling-includes-all-context
    return await ctx.session.create_message(messages=_user(text), max_tokens=100)


async def relay(ctx: Context, params: types.CreateMessageRequestParams):
    # A proxy forwarding the upstream server's own request unchanged.
    # ok: mcp-sampling-includes-all-context
    return await ctx.session.create_message(messages=params.messages, max_tokens=params.max_tokens, include_context=params.include_context)


async def sampling_callback(context, params: types.CreateMessageRequestParams):
    # Client side: reading the server's request, not making one.
    # ok: mcp-sampling-includes-all-context
    if params.include_context == "allServers":
        raise ValueError("this client doesn't share other servers' context")
    return types.CreateMessageResult(role="assistant", content=TextContent(text="ok"), model="local")


async def local_name(ctx: Context, text: str):
    # ok: mcp-sampling-includes-all-context
    include_context = "none"
    return await ctx.session.create_message(messages=_user(text), max_tokens=100, include_context=include_context)


async def local_wide(ctx: Context, text: str):
    include_context = WIDE_CONTEXT
    # ruleid: mcp-sampling-includes-all-context
    return await ctx.session.create_message(messages=_user(text), max_tokens=100, include_context=include_context)


# ok: mcp-sampling-includes-all-context
SUPPORTED = ("none", "thisServer", "allServers")
