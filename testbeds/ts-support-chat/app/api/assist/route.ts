import { openai } from "@ai-sdk/openai";
import { streamText } from "ai";
import { z } from "zod";
import { assistInstructions, toneGuide } from "@/lib/assist-prompts";
import { getTicket } from "@/lib/tickets";

const AssistRequest = z.object({
  ticketId: z.string().min(1),
  tone: z.enum(["friendly", "neutral", "formal"]).default("friendly"),
  agentName: z.string().min(1).max(80),
});

const RetoneRequest = z.object({
  draft: z.string().min(1).max(8000),
  tone: z.enum(["friendly", "neutral", "formal"]),
});

// Drafts a reply to the ticket for the agent, signed with the agent's display name.
export async function POST(req: Request) {
  const parsed = AssistRequest.safeParse(await req.json());
  if (!parsed.success) {
    return Response.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const { ticketId, tone, agentName } = parsed.data;
  const ticket = await getTicket(ticketId);
  const result = streamText({
    model: openai("gpt-4.1-mini"),
    instructions: assistInstructions({ tone, agentName }),
    prompt: `${ticket.subject}\n\n${ticket.body}`,
  });
  return result.toUIMessageStreamResponse();
}

// Re-tones an existing draft.
export async function PUT(req: Request) {
  const input = RetoneRequest.parse(await req.json());
  const result = streamText({
    model: openai("gpt-4.1-mini"),
    instructions: `Rewrite this support reply. ${toneGuide(input.tone)}`,
    prompt: input.draft,
  });
  return result.toUIMessageStreamResponse();
}
