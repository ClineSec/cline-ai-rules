import { openai } from "@ai-sdk/openai";
import { streamText } from "ai";
import { z } from "zod";
import { DRAFT_INSTRUCTIONS } from "@/lib/prompts";

const DraftRequest = z.object({ prompt: z.string().min(1).max(8000) });

export async function POST(req: Request) {
  const { prompt } = DraftRequest.parse(await req.json());

  const result = streamText({
    model: openai("gpt-4.1-mini"),
    instructions: DRAFT_INSTRUCTIONS,
    prompt,
  });

  return result.toUIMessageStreamResponse();
}
