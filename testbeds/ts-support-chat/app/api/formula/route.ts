import { openai } from "@ai-sdk/openai";
import { streamText } from "ai";
import { z } from "zod";

// Turns a support lead's description of a ticket-table column ("hours since the customer's
// last reply") into a JavaScript expression over `ticket`, for components/computed-field.tsx.
const FORMULA_INSTRUCTIONS = `Write one JavaScript expression over \`ticket\` (fields: createdAt,
lastCustomerReplyAt, priority, tags, messages) that computes the requested column. Reply with
the expression only, no code fences.`;

const FormulaRequest = z.object({ prompt: z.string().min(1).max(500) });

export async function POST(req: Request) {
  const { prompt } = FormulaRequest.parse(await req.json());

  const result = streamText({
    model: openai("gpt-4.1-mini"),
    instructions: FORMULA_INSTRUCTIONS,
    prompt,
  });

  return result.toTextStreamResponse();
}
