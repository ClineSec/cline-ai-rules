import Anthropic from "@anthropic-ai/sdk";
import { AIMessage, HumanMessage } from "@langchain/core/messages";
import { tool as lcTool } from "@langchain/core/tools";
import { ChatOpenAI } from "@langchain/openai";
import { openai } from "@ai-sdk/openai";
import {
  convertToModelMessages,
  createAgentUIStreamResponse,
  generateText,
  streamText,
  tool,
  ToolLoopAgent,
  type UIMessage,
} from "ai";
import express from "express";
import { Hono } from "hono";
import { createAgent } from "langchain";
import OpenAI from "openai";
import { z } from "zod";
import { db, loadChat, refundOrder } from "./store";

const anthropic = new Anthropic();
const client = new OpenAI();
const llm = new ChatOpenAI({ model: "gpt-5" });
const app = express();
const hono = new Hono();

const SYSTEM = "You are the Example Cloud billing assistant.";

const tools = {
  refund: tool({
    description: "Refund an order",
    inputSchema: z.object({ orderId: z.string(), amount: z.number() }),
    execute: async ({ orderId, amount }) => ({ orderId, amount, status: "queued" }),
  }),
};
const OPENAI_TOOLS = [
  { type: "function" as const, function: { name: "refund", parameters: { type: "object", properties: {} } } },
];
const ANTHROPIC_TOOLS = [{ name: "refund", description: "Refund an order", input_schema: { type: "object" as const } }];

const lookupOrder = lcTool(async ({ id }: { id: string }) => `order ${id}`, {
  name: "lookup_order",
  schema: z.object({ id: z.string() }),
});

const billingAgent = new ToolLoopAgent({ model: openai("gpt-5"), instructions: SYSTEM, tools });
const greeterAgent = new ToolLoopAgent({ model: openai("gpt-5"), instructions: "Say hello." });
const lcAgent = createAgent({ model: "openai:gpt-5", tools: [lookupOrder] });
const llmWithTools = llm.bindTools([lookupOrder]);

const UserTurns = z.object({
  messages: z.array(z.object({ role: z.literal("user"), content: z.string().max(4000) })),
});

// ---- Vercel AI SDK -------------------------------------------------------------------------

export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();
  const result = streamText({
    model: openai("gpt-5"),
    instructions: SYSTEM,
    // ruleid: client-message-roles-with-tools
    messages: await convertToModelMessages(messages),
    tools,
  });
  return result.toUIMessageStreamResponse();
}

export async function PUT(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();
  // No tools: a forged system turn only changes the caller's own chat.
  const result = streamText({
    model: openai("gpt-5"),
    instructions: SYSTEM,
    // ok: client-message-roles-with-tools
    messages: await convertToModelMessages(messages),
  });
  return result.toUIMessageStreamResponse();
}

export async function PATCH(req: Request) {
  // The AI SDK's "send only the last message" shape: history comes from storage, but the
  // client still picks the new message's role.
  const { message, id }: { message: UIMessage; id: string } = await req.json();
  const previous = await loadChat(id);
  const result = streamText({
    model: openai("gpt-5"),
    // ruleid: client-message-roles-with-tools
    messages: await convertToModelMessages([...previous, message]),
    tools,
  });
  return result.toUIMessageStreamResponse();
}

export async function DELETE(req: Request) {
  const body = await req.json();
  const { text } = await generateText({
    model: openai("gpt-5"),
    tools,
    // ruleid: client-message-roles-with-tools
    messages: body.messages.filter((m: { role: string }) => m.role !== "system"),
  });
  return Response.json({ text });
}

export async function OPTIONS(req: Request) {
  const body = await req.json();
  const { text } = await generateText({
    model: openai("gpt-5"),
    tools,
    // ok: client-message-roles-with-tools
    messages: body.messages.filter((m: { role: string }) => m.role === "user"),
  });
  return Response.json({ text });
}

export async function checked(req: Request) {
  const { messages } = await req.json();
  if (!messages.every((m: { role: string }) => m.role === "user")) {
    return Response.json({ error: "only user turns are accepted" }, { status: 400 });
  }
  return generateText({
    model: openai("gpt-5"),
    tools,
    // ok: client-message-roles-with-tools
    messages,
  });
}

export async function HEAD(req: Request) {
  const { messages, question } = await req.json();
  const last = messages[messages.length - 1];
  await generateText({
    model: openai("gpt-5"),
    tools,
    // ok: client-message-roles-with-tools
    messages: [{ role: "user", content: String(last.content) }],
  });
  return generateText({
    model: openai("gpt-5"),
    tools,
    // ok: client-message-roles-with-tools
    prompt: question,
  });
}

export async function GET(req: Request) {
  const { messages: turns } = await req.json();
  return generateText({
    model: openai("gpt-5"),
    tools,
    // ruleid: client-message-roles-with-tools
    messages: turns.map((m: { role: "user" | "assistant"; content: string }) => ({ role: m.role, content: m.content })),
  });
}

export async function rebuild(req: Request) {
  const { messages } = await req.json();
  await generateText({
    model: openai("gpt-5"),
    tools,
    // ok: client-message-roles-with-tools
    messages: messages.map((m: { role: string; content: string }) => ({
      role: m.role === "assistant" ? "assistant" : "user",
      content: String(m.content),
    })),
  });
  await generateText({
    model: openai("gpt-5"),
    tools,
    // ok: client-message-roles-with-tools
    messages: messages.map((m: { role: string; content: string }) => ({
      role: ["user", "assistant"].includes(m.role) ? m.role : "user",
      content: String(m.content),
    })),
  });
  await generateText({
    model: openai("gpt-5"),
    tools,
    // ruleid: client-message-roles-with-tools
    messages: messages.map((m: { role: string; content: string }) => ({
      role: ["user", "tool"].includes(m.role) ? m.role : "user",
      content: m.content,
    })),
  });
  return generateText({
    model: openai("gpt-5"),
    tools,
    // ruleid: client-message-roles-with-tools
    messages: messages.map((m: { role: string; content: string }) => ({ role: "user", ...m })),
  });
}

export async function stored(req: Request) {
  const { chatId, text } = await req.json();
  const history = await db.message.findMany({ where: { chatId } });
  return generateText({
    model: openai("gpt-5"),
    tools,
    // ok: client-message-roles-with-tools
    messages: [...history, { role: "user", content: text }],
  });
}

export async function validated(req: Request) {
  const { messages } = UserTurns.parse(await req.json());
  return generateText({
    model: openai("gpt-5"),
    tools,
    // ok: client-message-roles-with-tools
    messages,
  });
}

export async function switchedOff(req: Request) {
  const { messages } = await req.json();
  await generateText({
    model: openai("gpt-5"),
    tools,
    toolChoice: "none",
    // ok: client-message-roles-with-tools
    messages,
  });
  return generateText({
    model: openai("gpt-5"),
    tools: {},
    // ok: client-message-roles-with-tools
    messages,
  });
}

export async function agentRoute(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();
  await billingAgent.generate({
    // ruleid: client-message-roles-with-tools
    messages: await convertToModelMessages(messages),
  });
  await greeterAgent.generate({
    // ok: client-message-roles-with-tools
    messages: await convertToModelMessages(messages),
  });
  return createAgentUIStreamResponse({
    agent: billingAgent,
    // ruleid: client-message-roles-with-tools
    uiMessages: messages,
  });
}

// ---- OpenAI and Anthropic SDKs -------------------------------------------------------------

app.post("/chat", async (req, res) => {
  const { history } = req.body;
  const completion = await client.chat.completions.create({
    model: "gpt-5",
    // ruleid: client-message-roles-with-tools
    messages: [{ role: "developer", content: SYSTEM }, ...history],
    tools: OPENAI_TOOLS,
  });
  const message = completion.choices[0].message;
  // Refunds run here, with the billing service's credentials.
  for (const call of message.tool_calls ?? []) {
    await refundOrder(JSON.parse(call.function.arguments));
  }
  res.json(message);
});

app.post("/chat/plain", async (req, res) => {
  const completion = await client.chat.completions.create({
    model: "gpt-5",
    // ok: client-message-roles-with-tools
    messages: [{ role: "developer", content: SYSTEM }, ...req.body.history],
  });
  res.json(completion.choices[0].message);
});

app.post("/proxy", async (req, res) => {
  const completion = await client.chat.completions.create({
    // ruleid: client-message-roles-with-tools
    ...req.body,
    tools: OPENAI_TOOLS,
  });
  res.json(completion);
});

app.post("/responses", async (req, res) => {
  const response = await client.responses.create({
    model: "gpt-5",
    instructions: SYSTEM,
    // ruleid: client-message-roles-with-tools
    input: req.body.conversation,
    tools: [{ type: "function", name: "refund", parameters: {}, strict: false }],
  });
  const plain = await client.responses.create({
    model: "gpt-5",
    // ok: client-message-roles-with-tools
    input: req.body.question,
    tools: [{ type: "function", name: "refund", parameters: {}, strict: false }],
  });
  res.json({ response, plain });
});

hono.post("/claude", async (c) => {
  const body = await c.req.json();
  const msg = await anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 1024,
    system: SYSTEM,
    // ruleid: client-message-roles-with-tools
    messages: body.messages,
    tools: ANTHROPIC_TOOLS,
  });
  const plain = await anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 1024,
    system: SYSTEM,
    // ok: client-message-roles-with-tools
    messages: [{ role: "user", content: body.question }],
    tools: ANTHROPIC_TOOLS,
  });
  return c.json({ msg, plain });
});

// ---- LangChain.js --------------------------------------------------------------------------

app.post("/lc", async (req, res) => {
  // ruleid: client-message-roles-with-tools
  const reply = await llmWithTools.invoke(req.body.messages);
  // ok: client-message-roles-with-tools
  const single = await llm.bindTools([lookupOrder]).invoke(req.body.message);
  // ok: client-message-roles-with-tools
  const human = await llmWithTools.invoke([new HumanMessage(String(req.body.messages.at(-1)?.content))]);
  const rebuilt = await llmWithTools.invoke(
    // ok: client-message-roles-with-tools
    req.body.messages.map((m: { role: string; content: string }) =>
      m.role === "assistant" ? new AIMessage(String(m.content)) : new HumanMessage(String(m.content)),
    ),
  );
  const state = await lcAgent.invoke({
    // ruleid: client-message-roles-with-tools
    messages: req.body.messages,
  });
  res.json({ reply, single, human, rebuilt, state });
});

// ---- Settings objects spread into the call ---------------------------------------------------

const CHAT_SETTINGS = { model: openai("gpt-5"), tools, maxOutputTokens: 800 } satisfies Partial<
  Parameters<typeof generateText>[0]
>;
const PLAIN_SETTINGS = { model: openai("gpt-5"), maxOutputTokens: 800 };

export async function settingsRoute(req: Request) {
  const { messages } = await req.json();
  // ruleid: client-message-roles-with-tools
  await generateText({ ...CHAT_SETTINGS, messages });
  // ok: client-message-roles-with-tools
  return generateText({ ...PLAIN_SETTINGS, messages });
}

// ---- Tools the request supplies itself -------------------------------------------------------
// A model playground: the client sends the tool list and MCP servers too, so it already picks
// every tool, and a forged turn gets it nothing it couldn't ask for.

const withBillingKey = (t: { type: string }) => (t.type === "mcp" ? { ...t, headers: { authorization: "Bearer example" } } : t);

export async function playground(req: Request) {
  const { messages, tools, previousId } = await req.json();
  const params = { model: "gpt-5", input: messages, tools: (tools ?? []).map(withBillingKey), previous_response_id: previousId };
  // ok: client-message-roles-with-tools
  await client.responses.create(params);
  const enabled = tools.filter((t: { disabled?: boolean }) => !t.disabled);
  return client.responses.create({
    model: "gpt-5",
    // ok: client-message-roles-with-tools
    input: messages,
    tools: enabled,
  });
}

app.post("/playground", async (req, res) => {
  const completion = await client.chat.completions.create({
    model: "gpt-5",
    // ok: client-message-roles-with-tools
    messages: req.body.messages,
    tools: req.body.tools,
  });
  const { turns, tools: picked } = req.body;
  const again = await client.chat.completions.create({
    model: "gpt-5",
    // ok: client-message-roles-with-tools
    messages: turns,
    tools: picked,
  });
  res.json({ completion, again });
});

export async function scopedTools(req: Request) {
  // The request names an account, but the server picks the tools.
  const { messages, accountId } = await req.json();
  const allowed = OPENAI_TOOLS.filter((t) => t.function.name !== "refund" || accountId.startsWith("acct_"));
  return client.chat.completions.create({
    model: "gpt-5",
    // ruleid: client-message-roles-with-tools
    messages,
    tools: allowed,
  });
}

export async function toggledTools(req: Request) {
  // The chat UI's tool toggles only pick from the server's own tools, which still run here.
  const { messages, enabledTools } = await req.json();
  return client.chat.completions.create({
    model: "gpt-5",
    // ruleid: client-message-roles-with-tools
    messages,
    tools: OPENAI_TOOLS.filter((t) => enabledTools.includes(t.function.name)),
  });
}
