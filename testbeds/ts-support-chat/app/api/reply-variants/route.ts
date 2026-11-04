import { openai } from "@ai-sdk/openai";
import { generateText } from "ai";

const DRAFT_MODEL = openai("gpt-4.1-mini");

// Agent-assist: draft several versions of a reply so the agent can pick one. The console
// sends how long each version may be and how many to write.
export async function POST(req: Request) {
  const { ticket, maxTokens, variants } = await req.json();

  const drafts = await Promise.all(
    Array.from({ length: variants ?? 2 }, (_, i) =>
      generateText({
        model: DRAFT_MODEL,
        prompt: `Draft a reply to this support ticket:\n\n${ticket}`,
        maxOutputTokens: maxTokens,
        temperature: 0.4 + i * 0.2,
      }),
    ),
  );

  return Response.json({ drafts: drafts.map((d) => d.text) });
}

// Keeps drafting until the agent has the number of short replies they asked for.
export async function PUT(req: Request) {
  const { ticket, wanted } = await req.json();
  const kept: string[] = [];
  while (kept.length < wanted) {
    const { text } = await generateText({
      model: DRAFT_MODEL,
      prompt: `Draft a two-sentence reply to this support ticket:\n\n${ticket}`,
    });
    if (text.length <= 400) kept.push(text);
  }
  return Response.json({ replies: kept });
}
