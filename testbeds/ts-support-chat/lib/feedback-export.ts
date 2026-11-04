import { createReadStream } from "node:fs";
import { writeFile } from "node:fs/promises";
import path from "node:path";
import OpenAI from "openai";
import { prisma } from "./db";
import { SUPPORT_INSTRUCTIONS } from "./prompts";

// Thumbs-up answers are kept as chat-format fine-tuning examples for the next support model;
// the weekly export uploads only the ones QA has reviewed.
export const DATA_DIR = process.env.SUPPORT_DATA_DIR ?? path.join(process.cwd(), "var");
export const SFT_EXAMPLES_PATH = path.join(DATA_DIR, "sft", "thumbs-up.jsonl");
export const FEEDBACK_AUDIT_LOG = path.join(DATA_DIR, "audit", "feedback.jsonl");
export const BASE_MODEL = "gpt-4.1-mini-2025-04-14";

const openai = new OpenAI();

export type ChatTurn = { role: "user" | "assistant"; content: string };

export function toChatExample(turns: ChatTurn[]): string {
  const messages = [{ role: "system", content: SUPPORT_INSTRUCTIONS }, ...turns];
  return JSON.stringify({ messages }) + "\n";
}

// Weekly: reviewed thumbs-up conversations, rebuilt from the transcripts the server stored.
export async function exportReviewedFeedback(): Promise<string> {
  const rows = await prisma.feedback.findMany({
    where: { vote: "up", reviewedAt: { not: null } },
    include: { chat: { include: { messages: true } } },
  });
  const jsonl = rows
    .map((row) => toChatExample(row.chat.messages.map((m) => ({ role: m.role, content: m.text }))))
    .join("");
  const out = path.join(DATA_DIR, "exports", `reviewed-${Date.now()}.jsonl`);
  await writeFile(out, jsonl);
  const file = await openai.files.create({ file: createReadStream(out), purpose: "fine-tune" });
  const job = await openai.fineTuning.jobs.create({ training_file: file.id, model: BASE_MODEL, suffix: "support" });
  return job.id;
}
