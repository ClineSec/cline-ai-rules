import { appendFile, writeFile } from "node:fs/promises";
import fs from "node:fs";
import path from "node:path";
import express from "express";
import OpenAI, { toFile } from "openai";
import { Mistral } from "@mistralai/mistralai";
import Together from "together-ai";
import { requireAdmin } from "./auth";
import { getConversation, getUser } from "./db";

const openai = new OpenAI();
const mistral = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });
const together = new Together();
const app = express();

const TRAINING_FILE = "data/training_data.jsonl";
const FINE_TUNE = "fine-tune";

// ---- Uploads for fine-tuning ---------------------------------------------------------------

export async function POST(request: Request) {
  const form = await request.formData();
  const file = form.get("file") as File;
  // ruleid: user-content-to-fine-tuning-ts
  const uploaded = await openai.files.create({ file, purpose: "fine-tune" });
  return Response.json(await openai.fineTuning.jobs.create({ training_file: uploaded.id, model: "gpt-4o-mini" }));
}

app.post("/examples", async (req, res) => {
  const lines = req.body.examples.map((e: { messages: unknown }) => JSON.stringify({ messages: e.messages }));
  // ruleid: user-content-to-fine-tuning-ts
  const uploaded = await openai.files.create({ purpose: FINE_TUNE, file: await toFile(Buffer.from(lines.join("\n")), "train.jsonl") });
  res.json({ id: uploaded.id });
});

app.post("/examples/big", async (req, res) => {
  const blob = Buffer.from(req.body.jsonl);
  const upload = await openai.uploads.create({ bytes: blob.length, filename: "train.jsonl", mime_type: "text/jsonl", purpose: "fine-tune" });
  // ruleid: user-content-to-fine-tuning-ts
  await openai.uploads.parts.create(upload.id, { data: blob });
  res.json({ id: upload.id });
});

app.post("/examples/scratch", async (req, res) => {
  const tmp = path.join("/tmp", `upload-${Date.now()}.jsonl`);
  await writeFile(tmp, req.body.jsonl);
  // ruleid: user-content-to-fine-tuning-ts
  await openai.files.create({ file: fs.createReadStream(tmp), purpose: "fine-tune" });
  // ruleid: user-content-to-fine-tuning-ts
  await together.files.upload(tmp, "fine-tune");
  res.sendStatus(204);
});

app.post("/mistral/examples", async (req, res) => {
  const content = Buffer.from(JSON.stringify({ messages: req.body.messages }));
  // ruleid: user-content-to-fine-tuning-ts
  await mistral.files.upload({ file: { fileName: "train.jsonl", content }, purpose: "fine-tune" });
  res.sendStatus(204);
});

app.post("/files", async (req, res) => {
  // ok: user-content-to-fine-tuning-ts
  const uploaded = await openai.files.create({ file: await toFile(Buffer.from(req.body.text), "notes.txt"), purpose: "assistants" });
  res.json({ id: uploaded.id });
});

app.post("/admin/datasets", async (req, res) => {
  // ok: user-content-to-fine-tuning-ts
  const uploaded = await openai.files.create({ file: await toFile(Buffer.from(req.body.jsonl), "train.jsonl"), purpose: "fine-tune" });
  res.json({ id: uploaded.id });
});

app.post("/datasets", requireAdmin, async (req, res) => {
  // ok: user-content-to-fine-tuning-ts
  const uploaded = await openai.files.create({ file: await toFile(Buffer.from(req.body.jsonl), "train.jsonl"), purpose: "fine-tune" });
  res.json({ id: uploaded.id });
});

app.post("/my/fine-tunes", async (req, res) => {
  const user = await getUser(req.get("x-user-id"));
  const client = new OpenAI({ apiKey: user.openaiKey });
  // ok: user-content-to-fine-tuning-ts
  const uploaded = await client.files.create({ file: await toFile(Buffer.from(req.body.jsonl), "train.jsonl"), purpose: "fine-tune" });
  res.json({ id: uploaded.id });
});

export async function PUT(request: Request) {
  const session = await requireAdmin();
  const form = await request.formData();
  // ok: user-content-to-fine-tuning-ts
  const uploaded = await openai.files.create({ file: form.get("file") as File, purpose: "fine-tune" });
  return Response.json({ id: uploaded.id, by: session.user });
}

// ---- Feedback written to training data -----------------------------------------------------

app.post("/feedback", async (req, res) => {
  if (req.body.rating > 0) {
    // ruleid: user-content-to-fine-tuning-ts
    await appendFile(TRAINING_FILE, JSON.stringify({ messages: req.body.messages }) + "\n");
  }
  res.sendStatus(204);
});

app.post("/thumbs", (req, res) => {
  const out = path.join(process.cwd(), "data", "sft", "thumbs-up.jsonl");
  // ruleid: user-content-to-fine-tuning-ts
  fs.appendFileSync(out, JSON.stringify({ prompt: req.body.prompt, completion: req.body.answer }) + "\n");
  res.sendStatus(204);
});

app.post("/thumbs/stream", (req, res) => {
  const stream = fs.createWriteStream("data/finetune/feedback.jsonl", { flags: "a" });
  // ruleid: user-content-to-fine-tuning-ts
  stream.write(JSON.stringify(req.body) + "\n");
  res.sendStatus(204);
});

app.post("/feedback/logged", async (req, res) => {
  // ok: user-content-to-fine-tuning-ts
  await appendFile("logs/feedback-audit.jsonl", JSON.stringify(req.body) + "\n");
  res.sendStatus(204);
});

app.post("/feedback/stored", async (req, res) => {
  const convo = await getConversation(req.body.conversationId);
  // ok: user-content-to-fine-tuning-ts
  await appendFile(TRAINING_FILE, JSON.stringify({ messages: convo.messages, rating: Number(req.body.rating) }) + "\n");
  res.sendStatus(204);
});

// ---- A logger object built from a training-data path ---------------------------------------

class JsonlLog {
  constructor(private readonly file: string) {}

  async append(record: unknown) {
    await appendFile(this.file, JSON.stringify(record) + "\n");
  }
}

const SFT_DIR = "data/sft";
const sftLog = new JsonlLog(path.join(SFT_DIR, "thumbs.jsonl"));
const trainingLog = new JsonlLog(TRAINING_FILE);
const auditLog = new JsonlLog("logs/feedback-audit.jsonl");

app.post("/feedback/jsonl", async (req, res) => {
  // ok: user-content-to-fine-tuning-ts
  await auditLog.append({ chat: req.body.chatId, vote: req.body.vote });
  if (req.body.vote === "up") {
    // ruleid: user-content-to-fine-tuning-ts
    await sftLog.append({ messages: req.body.messages });
    // ruleid: user-content-to-fine-tuning-ts
    await trainingLog.append({ messages: req.body.messages });
  }
  res.sendStatus(204);
});
