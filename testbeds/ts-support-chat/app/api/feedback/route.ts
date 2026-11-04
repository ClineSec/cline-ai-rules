import { appendFile } from "node:fs/promises";
import { z } from "zod";
import { FEEDBACK_AUDIT_LOG, SFT_EXAMPLES_PATH, toChatExample } from "@/lib/feedback-export";

// Thumbs up / down from the chat window. The client sends back the turns it rated so the
// example matches what the customer saw.
const Vote = z.object({
  chatId: z.string(),
  vote: z.enum(["up", "down"]),
  turns: z.array(z.object({ role: z.enum(["user", "assistant"]), content: z.string() })),
});

export async function POST(request: Request) {
  const { chatId, vote, turns } = Vote.parse(await request.json());

  await appendFile(FEEDBACK_AUDIT_LOG, JSON.stringify({ chatId, vote, at: new Date().toISOString() }) + "\n");
  if (vote === "up") {
    await appendFile(SFT_EXAMPLES_PATH, toChatExample(turns));
  }
  return new Response(null, { status: 204 });
}
