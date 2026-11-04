import { openai } from "@ai-sdk/openai";
import { generateText } from "ai";
import { prisma } from "@/lib/db";

// Morning digest for a queue: /api/queues/billing/summary
export async function GET(request: Request, { params }: { params: Promise<{ queue: string }> }) {
  const { queue } = await params;
  const tickets = await prisma.ticket.findMany({
    where: { queue, status: "open" },
    select: { id: true, subject: true, openedAt: true },
    take: 50,
  });
  // Kept as one object so the digest job can log exactly what was sent.
  const digestRequest = {
    model: openai("gpt-4.1-mini"),
    instructions: `Summarize the open tickets in the ${queue} queue for the support lead. Group them by root cause.`,
    prompt: JSON.stringify(tickets),
    maxOutputTokens: 600,
  };
  const { text } = await generateText(digestRequest);
  return Response.json({ queue, summary: text });
}
