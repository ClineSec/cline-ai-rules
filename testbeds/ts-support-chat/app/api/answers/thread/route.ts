import { openai } from "@ai-sdk/openai";
import { generateText } from "ai";
import { prisma } from "@/lib/db";

// Shift handoff: a summary of each open thread for the next agent on shift.
export async function POST(req: Request) {
  const { ticketId } = (await req.json()) as { ticketId: string };
  const thread = await prisma.ticketThread.findUnique({
    where: { ticketId },
    include: { messages: { orderBy: { createdAt: "asc" } } },
  });
  const transcript = (thread?.messages ?? []).map((m) => `${m.authorRole}: ${m.body}`).join("\n");
  const { text } = await generateText({
    model: openai("gpt-4.1-mini"),
    system: `Summarize this support thread for the next agent on shift in five bullets.\n\n${transcript}`,
    prompt: "Summary:",
  });
  return Response.json({ summary: text });
}

// Thread header for the handoff board: the assistant greets in the workspace's configured voice.
export async function GET(req: Request) {
  const ticketId = new URL(req.url).searchParams.get("ticketId") ?? "";
  const [settings, thread] = await Promise.all([
    prisma.workspaceSettings.findFirst(),
    prisma.ticketThread.findUnique({ where: { ticketId }, select: { status: true, priority: true, messageCount: true } }),
  ]);
  const { text } = await generateText({
    model: openai("gpt-4.1-mini"),
    system: `${settings?.assistantPersona ?? "You are the support assistant."} The thread is ${thread?.status}, priority ${thread?.priority}, ${thread?.messageCount} messages.`,
    prompt: "Write a one-line header for the handoff board.",
  });
  return Response.json({ header: text });
}
