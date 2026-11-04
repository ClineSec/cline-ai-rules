import express from "express";
import { load } from "@langchain/core/load";
import * as classicLoad from "langchain/load";
import type { ChatPromptTemplate } from "@langchain/core/prompts";

const app = express();
app.use(express.json());

const SAVED_PROMPTS: Record<string, string> = { weekly: "{}" };

app.post("/prompts/import", async (req, res) => {
  // ruleid: langchain-load-untrusted-input-ts
  const prompt = await load<ChatPromptTemplate>(JSON.stringify(req.body.prompt));
  res.json({ variables: prompt.inputVariables });
});

export async function POST(request: Request) {
  const body = await request.json();
  // ruleid: langchain-load-untrusted-input-ts
  const chain = await classicLoad.load(JSON.stringify(body.chain), { OPENAI_API_KEY: "sk-test-invalid" });
  return Response.json({ kind: typeof chain });
}

app.post("/prompts/import-text", async (req, res) => {
  const text = String(req.body.manifest);
  // ruleid: langchain-load-untrusted-input-ts
  const prompt = await load(text, { maxDepth: 10 });
  res.json({ ok: Boolean(prompt) });
});

// --- near misses ------------------------------------------------------------------------

app.post("/prompts/run", async (req, res) => {
  const name = req.body.name as string;
  // ok: langchain-load-untrusted-input-ts
  const prompt = await load(SAVED_PROMPTS[name] ?? "{}");
  res.json({ ok: Boolean(prompt) });
});

app.post("/prompts/restore", async (req, res) => {
  // Reported by langchain-load-unsafe-objects-ts instead.
  // ok: langchain-load-untrusted-input-ts
  const prompt = await load(JSON.stringify(req.body), { secretsFromEnv: true });
  res.json({ ok: Boolean(prompt) });
});

app.post("/prompts/preview", async (req, res) => {
  // ok: langchain-load-untrusted-input-ts
  const parsed = JSON.parse(JSON.stringify(req.body));
  res.json({ keys: Object.keys(parsed) });
});
