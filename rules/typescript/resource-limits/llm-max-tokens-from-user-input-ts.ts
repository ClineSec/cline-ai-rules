import Anthropic from "@anthropic-ai/sdk";
import { openai as openaiProvider } from "@ai-sdk/openai";
import { Agent, run } from "@openai/agents";
import { ChatAnthropic } from "@langchain/anthropic";
import { ChatOpenAI } from "@langchain/openai";
import { generateText, isStepCount, streamText } from "ai";
import express from "express";
import OpenAI from "openai";
import { z } from "zod";

const app = express();
app.use(express.json());
const client = new OpenAI();
const claude = new Anthropic();

const MAX_TOKENS = 2048;
const PLAN_LIMITS: Record<string, number> = { free: 512, pro: 4096 };

const AskBody = z.object({
  question: z.string(),
  maxTokens: z.number().int().positive().default(512),
});

const BoundedAsk = z.object({
  question: z.string(),
  maxTokens: z.number().int().min(1).max(4096).default(512),
  variants: z.coerce.number().int().lte(3).default(1),
});

function clampTokens(n: number): number {
  return Math.max(1, Math.min(n, MAX_TOKENS));
}

// ---- OpenAI / Anthropic over Express ------------------------------------------------------

app.post("/ask", async (req, res) => {
  const completion = await client.chat.completions.create({
    model: "gpt-5-mini",
    messages: [{ role: "user", content: req.body.question }],
    // ruleid: llm-max-tokens-from-user-input-ts
    max_completion_tokens: req.body.maxTokens,
    // ruleid: llm-max-tokens-from-user-input-ts
    n: req.body.n,
  });
  res.json(completion);
});

app.post("/ask/responses", async (req, res) => {
  const { max_output_tokens } = req.body;
  // ruleid: llm-max-tokens-from-user-input-ts
  const out = await client.responses.create({ model: "gpt-5-mini", input: "hi", max_output_tokens });
  res.json(out);
});

app.post("/ask/number", async (req, res) => {
  const tokens = Number(req.query.max_tokens ?? 512);
  // ruleid: llm-max-tokens-from-user-input-ts
  const msg = await claude.messages.create({ model: "claude-sonnet-4-5", max_tokens: tokens, messages: [] });
  res.json(msg);
});

app.post("/ask/min", async (req, res) => {
  const tokens = Math.min(Number(req.body.maxTokens), MAX_TOKENS);
  // ok: llm-max-tokens-from-user-input-ts
  const msg = await claude.messages.create({ model: "claude-sonnet-4-5", max_tokens: tokens, messages: [] });
  res.json(msg);
});

app.post("/ask/clamp", async (req, res) => {
  // ok: llm-max-tokens-from-user-input-ts
  const msg = await claude.messages.create({ model: "claude-sonnet-4-5", max_tokens: clampTokens(req.body.maxTokens), messages: [] });
  res.json(msg);
});

app.post("/ask/checked", async (req, res) => {
  const tokens = req.body.maxTokens;
  if (tokens > MAX_TOKENS) {
    return res.status(400).json({ error: "max_tokens too large" });
  }
  // ok: llm-max-tokens-from-user-input-ts
  const msg = await claude.messages.create({ model: "claude-sonnet-4-5", max_tokens: tokens, messages: [] });
  res.json(msg);
});

app.post("/ask/ternary", async (req, res) => {
  const asked = req.body.maxTokens;
  const tokens = asked > MAX_TOKENS ? MAX_TOKENS : asked;
  // ok: llm-max-tokens-from-user-input-ts
  const msg = await claude.messages.create({ model: "claude-sonnet-4-5", max_tokens: tokens, messages: [] });
  res.json(msg);
});

app.post("/ask/plan", async (req, res) => {
  // ok: llm-max-tokens-from-user-input-ts
  const msg = await claude.messages.create({ model: "claude-sonnet-4-5", max_tokens: PLAN_LIMITS[req.body.plan], messages: [] });
  res.json(msg);
});

app.post("/ask/echo", async (req, res) => {
  // ok: llm-max-tokens-from-user-input-ts
  res.json({ max_tokens: req.body.maxTokens, ok: true });
});

app.post("/ask/params", async (req, res) => {
  const params = {
    model: "gpt-5-mini",
    messages: [],
    // ruleid: llm-max-tokens-from-user-input-ts
    max_tokens: req.body.maxTokens,
  };
  const completion = await client.chat.completions.create(params);
  res.json(completion);
});

app.post("/ask/fetch", async (req, res) => {
  const r = await fetch("https://api.example.invalid/v1/chat/completions", {
    method: "POST",
    // ruleid: llm-max-tokens-from-user-input-ts
    body: JSON.stringify({ model: "m", messages: [], max_tokens: req.body.maxTokens }),
  });
  res.json(await r.json());
});

app.post("/variants", async (req, res) => {
  const drafts = [];
  // ruleid: llm-max-tokens-from-user-input-ts
  for (let i = 0; i < req.body.variants; i++) {
    drafts.push(await client.chat.completions.create({ model: "gpt-5-mini", messages: [], max_tokens: 256 }));
  }
  res.json(drafts);
});

app.post("/variants/while", async (req, res) => {
  const drafts = [];
  let i = 0;
  // ruleid: llm-max-tokens-from-user-input-ts
  while (i < req.body.variants) {
    drafts.push(await generateText({ model: openaiProvider("gpt-5-mini"), prompt: "x" }));
    i++;
  }
  res.json(drafts);
});

app.post("/variants/while-capped", async (req, res) => {
  const wanted = Math.min(Number(req.body.variants), 3);
  const drafts = [];
  // ok: llm-max-tokens-from-user-input-ts
  while (drafts.length < wanted) {
    drafts.push(await generateText({ model: openaiProvider("gpt-5-mini"), prompt: "x" }));
  }
  res.json(drafts);
});

app.post("/variants/while-clamped", async (req, res) => {
  const wanted = clampTokens(req.body.variants);
  let i = 0;
  // ok: llm-max-tokens-from-user-input-ts
  while (i < wanted) {
    await claude.messages.create({ model: "claude-sonnet-4-5", max_tokens: 256, messages: [] });
    i++;
  }
  res.json({ ok: true });
});

app.post("/variants/while-true", async (req, res) => {
  let attempts = 0;
  // ok: llm-max-tokens-from-user-input-ts
  while (true) {
    const out = await generateText({ model: openaiProvider("gpt-5-mini"), prompt: req.body.question });
    if (out.finishReason === "stop" || ++attempts >= 3) return res.json(out);
  }
});

app.post("/pages", async (req, res) => {
  const pages = [];
  // ok: llm-max-tokens-from-user-input-ts
  for (let i = 0; i < req.body.pages; i++) {
    pages.push(i * 2);
  }
  res.json(pages);
});

// ---- Next.js route handlers on the AI SDK, LangChain.js, and agents -------------------------

export async function POST(request: Request) {
  const body = AskBody.parse(await request.json());
  const result = streamText({
    model: openaiProvider("gpt-5-mini"),
    prompt: body.question,
    // ruleid: llm-max-tokens-from-user-input-ts
    maxOutputTokens: body.maxTokens,
  });
  return result.toTextStreamResponse();
}

export async function PUT(request: Request) {
  const { question, maxTokens, variants } = BoundedAsk.parse(await request.json());
  const result = await generateText({
    model: openaiProvider("gpt-5-mini"),
    prompt: question,
    // ok: llm-max-tokens-from-user-input-ts
    maxOutputTokens: maxTokens,
  });
  // ok: llm-max-tokens-from-user-input-ts
  const more = await Promise.all(Array.from({ length: variants }, () => generateText({ model: openaiProvider("gpt-5-mini"), prompt: question })));
  return Response.json({ text: result.text, more });
}

export async function PATCH(request: Request) {
  const parsed = BoundedAsk.safeParse(await request.json());
  if (!parsed.success) return new Response("bad request", { status: 400 });
  // ok: llm-max-tokens-from-user-input-ts
  const llm = new ChatOpenAI({ model: "gpt-5-mini", maxTokens: parsed.data.maxTokens });
  return Response.json(await llm.invoke(parsed.data.question));
}

export async function DELETE(request: Request) {
  const body = await request.json();
  // ruleid: llm-max-tokens-from-user-input-ts
  const llm = new ChatAnthropic({ model: "claude-sonnet-4-5", maxTokens: body.maxTokens });
  // ruleid: llm-max-tokens-from-user-input-ts
  const drafts = await Promise.all(Array.from({ length: body.variants }, () => llm.invoke(body.question)));
  return Response.json(drafts);
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const steps = Number(url.searchParams.get("steps") ?? 5);
  const agent = new Agent({ name: "helper", instructions: "Answer briefly." });
  // ruleid: llm-max-tokens-from-user-input-ts
  const out = await run(agent, url.searchParams.get("q") ?? "", { maxTurns: steps });
  const more = await generateText({
    model: openaiProvider("gpt-5-mini"),
    prompt: "x",
    // ruleid: llm-max-tokens-from-user-input-ts
    stopWhen: isStepCount(steps),
  });
  return Response.json({ out: out.finalOutput, more: more.text });
}
