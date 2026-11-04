const fs = require("node:fs");
const { Hono } = require("hono");
const OpenAI = require("openai");
const { toFile } = require("openai");

const client = new OpenAI();
const app = new Hono();
const SFT_DIR = "data/sft";

// Next.js pages API route.
module.exports.feedback = async function handler(req, res) {
  const { messages, rating } = req.body;
  if (rating === "up") {
    // ruleid: user-content-to-fine-tuning-ts
    await fs.promises.appendFile(`${SFT_DIR}/thumbs-up.jsonl`, JSON.stringify({ messages }) + "\n");
  }
  res.status(204).end();
};

app.post("/corrections", async (c) => {
  const body = await c.req.json();
  const jsonl = body.corrections.map((x) => JSON.stringify({ messages: x })).join("\n");
  // ruleid: user-content-to-fine-tuning-ts
  const file = await client.files.create({ file: await toFile(Buffer.from(jsonl), "corrections.jsonl"), purpose: "fine-tune" });
  return c.json({ id: file.id });
});

app.post("/corrections/eval", async (c) => {
  const body = await c.req.json();
  // ok: user-content-to-fine-tuning-ts
  const file = await client.files.create({ file: await toFile(Buffer.from(body.jsonl), "eval.jsonl"), purpose: "evals" });
  return c.json({ id: file.id });
});

app.post("/corrections/queue", async (c) => {
  const body = await c.req.json();
  // ok: user-content-to-fine-tuning-ts
  fs.appendFileSync("data/review-queue/corrections.jsonl", JSON.stringify(body) + "\n");
  return c.body(null, 204);
});
