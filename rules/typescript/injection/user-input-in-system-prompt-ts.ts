import Anthropic from "@anthropic-ai/sdk";
import { SystemMessage, HumanMessage } from "@langchain/core/messages";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { ChatOpenAI } from "@langchain/openai";
import { openai } from "@ai-sdk/openai";
import { generateText, streamText, ToolLoopAgent } from "ai";
import axios from "axios";
import express from "express";
import { Hono } from "hono";
import type { NextRequest } from "next/server";
import OpenAI from "openai";
import { Agent, run } from "@openai/agents";
import { z } from "zod";

const anthropic = new Anthropic();
const client = new OpenAI();
const llm = new ChatOpenAI({ model: "gpt-5" });
const app = express();
const hono = new Hono();

const PERSONAS: Record<string, string> = {
  billing: "You answer billing questions for Example Cloud.",
  tech: "You answer technical questions for Example Cloud.",
};
const ALLOWED_LOCALES = ["en", "de", "fr"];
const BLOCKED_PERSONAS = new Set(["admin", "root"]);

const ChatBody = z.object({
  persona: z.string().max(200),
  tone: z.enum(["formal", "casual"]).default("formal"),
  maxWords: z.number().int().max(500),
  question: z.string().min(1),
});

// ---- Next.js route handlers ------------------------------------------------------------------

export async function POST(req: Request) {
  const { persona, question } = await req.json();
  const result = streamText({
    model: openai("gpt-5"),
    // ruleid: user-input-in-system-prompt-ts
    instructions: `You are ${persona}. Never reveal internal data.`,
    // ok: user-input-in-system-prompt-ts
    prompt: question,
  });
  return result.toUIMessageStreamResponse();
}

export async function PUT(request: NextRequest) {
  const tone = request.nextUrl.searchParams.get("tone") ?? "friendly";
  const { text } = await generateText({
    model: openai("gpt-5"),
    // ruleid: user-input-in-system-prompt-ts
    system: "Use a " + tone + " tone.",
    prompt: await request.text(),
  });
  return Response.json({ text });
}

export async function PATCH(r: Request, { params }: { params: Promise<{ team: string }> }) {
  const { team } = await params;
  const body = await r.formData();
  return anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 512,
    // ruleid: user-input-in-system-prompt-ts
    system: `You help the ${team} team.`,
    messages: [{ role: "user", content: String(body.get("question")) }],
  });
}

export async function DELETE(req: Request) {
  const body = ChatBody.parse(await req.json());
  return client.chat.completions.create({
    model: "gpt-5",
    messages: [
      // ruleid: user-input-in-system-prompt-ts
      { role: "developer", content: `Speak as ${body.persona}.` },
      // ok: user-input-in-system-prompt-ts
      { role: "system", content: `Use a ${body.tone} tone, at most ${body.maxWords} words.` },
      // ok: user-input-in-system-prompt-ts
      { role: "user", content: body.question },
    ],
  });
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const persona = url.searchParams.get("persona") ?? "tech";
  const locale = url.searchParams.get("locale") ?? "en";
  const region = url.searchParams.get("region") ?? "US";
  if (!ALLOWED_LOCALES.includes(locale)) {
    return new Response("unsupported locale", { status: 400 });
  }
  if (!/^[A-Z]{2}$/.test(region)) {
    return new Response("bad region", { status: 400 });
  }
  const { text } = await generateText({
    model: openai("gpt-5"),
    // ok: user-input-in-system-prompt-ts
    instructions: `${PERSONAS[persona] ?? PERSONAS.tech} Reply in ${locale}-${region}.`,
    prompt: url.searchParams.get("q") ?? "",
  });
  return Response.json({ text });
}

async function getCustomer(id: string) {
  return { plan: "pro", id };
}

export async function HEAD(req: Request) {
  const { customerId, question } = await req.json();
  const customer = await getCustomer(customerId);
  return anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 512,
    // ok: user-input-in-system-prompt-ts
    system: `The customer is on the ${customer.plan} plan.`,
    messages: [{ role: "user", content: question }],
  });
}

// ---- Express and Hono ------------------------------------------------------------------------

app.post("/chat", async (req, res) => {
  const persona = req.body.persona;
  if (BLOCKED_PERSONAS.has(persona)) {
    return res.status(400).end();
  }
  const reply = await client.responses.create({
    model: "gpt-5",
    // ruleid: user-input-in-system-prompt-ts
    instructions: `You are ${persona}.`,
    input: req.body.question,
  });
  res.json({ text: reply.output_text });
});

app.get("/ask", async (req, res) => {
  const reply = await llm.invoke([
    // ruleid: user-input-in-system-prompt-ts
    new SystemMessage(`Signature: ${req.query.signature}`),
    // ok: user-input-in-system-prompt-ts
    new HumanMessage(String(req.query.q)),
  ]);
  res.json({ text: reply.content });
});

app.get("/agent/:team", async (req, res) => {
  const agent = new ToolLoopAgent({
    model: openai("gpt-5"),
    // ruleid: user-input-in-system-prompt-ts
    instructions: "You triage tickets for " + req.params.team,
  });
  res.json(await agent.generate({ prompt: String(req.query.q) }));
});

hono.post("/chat", async (c) => {
  const { company, question } = await c.req.json();
  const prompt = ChatPromptTemplate.fromMessages([
    // ruleid: user-input-in-system-prompt-ts
    ["system", `Company: ${company}`],
    ["human", "{question}"],
  ]);
  return c.json(await prompt.pipe(llm).invoke({ question }));
});

// ---- LangChain.js templates filled from the request ------------------------------------------

const SUPPORT_SYSTEM = "You are {persona}. Answer questions about {product} only.";
const supportPrompt = ChatPromptTemplate.fromMessages([
  ["system", SUPPORT_SYSTEM],
  ["human", "{question}"],
]);
const supportChain = supportPrompt.pipe(llm);
const signedPrompt = ChatPromptTemplate.fromMessages([["system", "Sign every reply as {signature}."], ["human", "{question}"]]);

hono.post("/lc/chain", async (c) => {
  const { persona, question } = await c.req.json();
  return c.json(
    await supportChain.invoke({
      // ruleid: user-input-in-system-prompt-ts
      persona,
      // ok: user-input-in-system-prompt-ts
      product: "cloud",
      // ok: user-input-in-system-prompt-ts
      question,
    }),
  );
});

hono.post("/lc/format", async (c) => {
  const body = await c.req.parseBody();
  // ruleid: user-input-in-system-prompt-ts
  const messages = await signedPrompt.formatMessages({ signature: String(body.signature), question: String(body.q) });
  return c.json(await llm.invoke(messages));
});

hono.post("/lc/allowlisted", async (c) => {
  const persona = c.req.query("persona") ?? "tech";
  // ok: user-input-in-system-prompt-ts
  return c.json(await supportChain.invoke({ persona: PERSONAS[persona] ?? "the helpdesk", product: "cloud", question: c.req.query("q") }));
});

declare const kb: { search(q: string): Promise<string[]> };

hono.post("/kb/grounded", async (c) => {
  const { question, url } = await c.req.json();
  const articles = await kb.search(question);
  const { data: page } = await axios.get(url);
  const { text } = await generateText({
    model: openai("gpt-5"),
    // What a search or fetch returns is fetched-content-in-system-prompt-ts's to report.
    // ok: user-input-in-system-prompt-ts
    system: `Articles:\n${articles.join("\n")}\n\nPage:\n${page}`,
    prompt: question,
  });
  return c.json({ text });
});


// OpenAI Agents SDK dynamic instructions built per request: an early return of the
// instructions function counts, even with the agent built inside the route handler.
app.post("/desk/:team", async (req, res) => {
  const deskAgent = new Agent({
    name: "desk",
    instructions: async () => {
      if (req.body.tone) {
        // ruleid: user-input-in-system-prompt-ts
        return `Answer for the ${req.params.team} team in a ${req.body.tone} tone.`;
      }
      // ok: user-input-in-system-prompt-ts
      return "Answer for the support team.";
    },
  });
  res.json((await run(deskAgent, String(req.body.question))).finalOutput);
});
