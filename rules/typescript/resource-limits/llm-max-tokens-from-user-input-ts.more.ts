"use server";

import { query } from "@anthropic-ai/claude-agent-sdk";
import { GoogleGenAI } from "@google/genai";
import { initChatModel } from "langchain/chat_models/universal";
import { Agent } from "@mastra/core/agent";
import axios from "axios";
import { Hono } from "hono";
import { DraftRequest } from "./schemas";

const genai = new GoogleGenAI({});
const hono = new Hono();
const helper = new Agent({ name: "helper", instructions: "Answer briefly.", model: "openai/gpt-5-mini" });

hono.post("/gemini", async (c) => {
  const body = await c.req.json();
  const out = await genai.models.generateContent({
    model: "gemini-2.5-flash",
    contents: body.question,
    // ruleid: llm-max-tokens-from-user-input-ts
    config: { maxOutputTokens: body.maxTokens, temperature: 0.2 },
  });
  return c.json(out);
});

hono.post("/proxy", async (c) => {
  const body = await c.req.json();
  // ruleid: llm-max-tokens-from-user-input-ts
  const r = await axios.post("https://api.example.invalid/v1/messages", { model: "m", max_tokens: body.max_tokens });
  return c.json(r.data);
});

export async function draftReply(question: string, maxTokens: number) {
  // ruleid: llm-max-tokens-from-user-input-ts
  const model = await initChatModel("openai:gpt-5-mini", { maxTokens });
  return (await model.invoke(question)).content;
}

export async function runOpsAgent(prompt: string, turns: number) {
  const messages = [];
  // ruleid: llm-max-tokens-from-user-input-ts
  for await (const m of query({ prompt, options: { maxTurns: turns } })) {
    messages.push(m);
  }
  return messages;
}

export async function askHelper(prompt: string, steps: number) {
  // ruleid: llm-max-tokens-from-user-input-ts
  return helper.generate(prompt, { maxSteps: steps });
}

export async function askHelperCapped(prompt: string, steps: number) {
  // ok: llm-max-tokens-from-user-input-ts
  return helper.generate(prompt, { maxSteps: Math.min(steps, 8) });
}

export async function runGraph(graph: { invoke: Function }, input: string, limit: number) {
  // ruleid: llm-max-tokens-from-user-input-ts
  return graph.invoke({ input }, { recursionLimit: limit });
}

hono.post("/drafts", async (c) => {
  // The schema lives in another module, which may bound maxTokens.
  const body = DraftRequest.parse(await c.req.json());
  // ok: llm-max-tokens-from-user-input-ts
  const out = await genai.models.generateContent({ model: "gemini-2.5-flash", contents: body.question, config: { maxOutputTokens: body.maxTokens } });
  return c.json(out);
});

hono.post("/drafts/raw", async (c) => {
  const body = JSON.parse(await c.req.text());
  // ruleid: llm-max-tokens-from-user-input-ts
  const out = await genai.models.generateContent({ model: "gemini-2.5-flash", contents: body.question, config: { maxOutputTokens: body.maxTokens } });
  return c.json(out);
});
