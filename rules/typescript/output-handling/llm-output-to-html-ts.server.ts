// Server-side HTML responses built from model output: Express, Node http, Fetch Response, Hono.
import express from "express";
import http from "node:http";
import { Hono } from "hono";
import OpenAI from "openai";
import Anthropic from "@anthropic-ai/sdk";
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { marked } from "marked";
import type { NextApiRequest, NextApiResponse } from "next";

const client = new OpenAI();
const anthropic = new Anthropic();
const app = express();

app.get("/answer", async (req, res) => {
  const completion = await client.chat.completions.create({
    model: "gpt-4.1",
    messages: [{ role: "user", content: String(req.query.q) }],
  });
  const answer = completion.choices[0].message.content ?? "";
  // ruleid: llm-output-to-html-ts
  res.send(marked.parse(answer));
});

app.get("/answer-status", async (req, res) => {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: String(req.query.q) });
  // ruleid: llm-output-to-html-ts
  res.status(200).send(`<article>${text}</article>`);
});

app.get("/answer.txt", async (req, res) => {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: String(req.query.q) });
  res.type("text/plain");
  // ok: llm-output-to-html-ts
  res.send(text);
});

app.get("/answer-plain", async (req, res) => {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: String(req.query.q) });
  // ok: llm-output-to-html-ts
  res.status(200).type("txt").send(text);
});

app.get("/answer-header", async (req, res) => {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: String(req.query.q) });
  res.set("Content-Type", "text/plain; charset=utf-8");
  // ok: llm-output-to-html-ts
  res.send(text);
});

app.get("/answer.json", async (req, res) => {
  const result = await generateText({ model: openai("gpt-4.1"), prompt: String(req.query.q) });
  // ok: llm-output-to-html-ts
  res.json({ answer: result.text });
  // ok: llm-output-to-html-ts
  res.send({ answer: result.text });
});

app.get("/raw-result", async (req, res) => {
  const msg = await anthropic.messages.create({
    model: "claude-sonnet-4-5",
    max_tokens: 512,
    messages: [{ role: "user", content: String(req.query.q) }],
  });
  // ok: llm-output-to-html-ts
  res.send(msg);
});

app.get("/stream", async (req, res) => {
  res.setHeader("Content-Type", "text/html; charset=utf-8");
  const stream = await client.chat.completions.create({
    model: "gpt-4.1",
    messages: [{ role: "user", content: String(req.query.q) }],
    stream: true,
  });
  for await (const chunk of stream) {
    // ruleid: llm-output-to-html-ts
    res.write(chunk.choices[0]?.delta?.content || "");
  }
  res.end();
});

app.get("/stream.txt", async (req, res) => {
  res.setHeader("Content-Type", "text/plain; charset=utf-8");
  const stream = await client.chat.completions.create({
    model: "gpt-4.1",
    messages: [{ role: "user", content: String(req.query.q) }],
    stream: true,
  });
  for await (const chunk of stream) {
    // ok: llm-output-to-html-ts
    res.write(chunk.choices[0]?.delta?.content || "");
  }
  res.end();
});

http.createServer(async (req, res) => {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: req.url ?? "" });
  res.writeHead(200, { "Content-Type": "text/html" });
  // ruleid: llm-output-to-html-ts
  res.end(text);
});

export async function GET(request: Request) {
  const prompt = new URL(request.url).searchParams.get("q") ?? "";
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt });
  // ruleid: llm-output-to-html-ts
  return new Response(text, { headers: { "Content-Type": "text/html; charset=utf-8" } });
}

export async function POST(request: Request) {
  const { prompt } = await request.json();
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt });
  const headers = new Headers();
  headers.set("content-type", "text/html");
  // ruleid: llm-output-to-html-ts
  return new Response(text, { status: 200, headers });
}

export async function PUT(request: Request) {
  const { prompt } = await request.json();
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt });
  // ok: llm-output-to-html-ts
  return new Response(text);
}

export async function PATCH(request: Request) {
  const { prompt } = await request.json();
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt });
  // ok: llm-output-to-html-ts
  return new Response(text, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
}

const hono = new Hono();

hono.get("/preview", async (c) => {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: c.req.query("q") ?? "" });
  // ruleid: llm-output-to-html-ts
  return c.html(text);
});

hono.get("/preview.txt", async (c) => {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: c.req.query("q") ?? "" });
  // ok: llm-output-to-html-ts
  return c.text(text);
});

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: String(req.query.q) });
  // ok: llm-output-to-html-ts
  res.send(text);
}

function relay(ws: WebSocket, text: string) {
  // ok: llm-output-to-html-ts
  ws.send(text);
}
