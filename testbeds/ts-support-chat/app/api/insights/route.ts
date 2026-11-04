import OpenAI from "openai";
import { z } from "zod";
import { prisma } from "@/lib/db";

const openai = new OpenAI();

const InsightRequest = z.object({ question: z.string().min(1).max(2000) });

// Columns a breakdown may group by; the model names one.
const GROUP_COLUMNS: Record<string, string> = {
  queue: '"queue"',
  channel: '"channel"',
  week: "date_trunc('week', \"openedAt\")",
};

async function plan(question: string) {
  const completion = await openai.chat.completions.create({
    model: "gpt-4.1-mini",
    response_format: { type: "json_object" },
    messages: [
      {
        role: "system",
        content:
          'Plan a ticket breakdown. Return JSON {"queue": string, "groupBy": a SQL expression over "Ticket"}.',
      },
      { role: "user", content: question },
    ],
  });
  return JSON.parse(completion.choices[0].message.content ?? "{}") as { queue: string; groupBy: string };
}

export async function POST(req: Request) {
  const { question } = InsightRequest.parse(await req.json());
  const completion = await openai.chat.completions.create({
    model: "gpt-4.1-mini",
    response_format: { type: "json_object" },
    messages: [
      {
        role: "system",
        content:
          'Plan a ticket breakdown. Return JSON {"queue": string, "groupBy": a SQL expression over "Ticket"}.',
      },
      { role: "user", content: question },
    ],
  });
  const breakdown = JSON.parse(completion.choices[0].message.content ?? "{}");
  const rows = await prisma.$queryRawUnsafe(
    `SELECT ${breakdown.groupBy} AS bucket, count(*)::int AS tickets FROM "Ticket" WHERE "queue" = $1 GROUP BY 1 ORDER BY 2 DESC`,
    breakdown.queue,
  );
  return Response.json({ rows });
}

export async function PUT(req: Request) {
  const { question } = InsightRequest.parse(await req.json());
  const breakdown = await plan(question);
  const bucket = GROUP_COLUMNS[breakdown.groupBy] ?? GROUP_COLUMNS.queue;
  const rows = await prisma.$queryRawUnsafe(
    `SELECT ${bucket} AS bucket, count(*)::int AS tickets FROM "Ticket" WHERE "queue" = $1 GROUP BY 1`,
    breakdown.queue,
  );
  const total = await prisma.$queryRaw`SELECT count(*)::int AS tickets FROM "Ticket" WHERE "queue" = ${breakdown.queue}`;
  return Response.json({ rows, total });
}
