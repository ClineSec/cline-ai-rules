import { openai } from "@ai-sdk/openai";
import { generateObject, generateText } from "ai";
import { sql } from "drizzle-orm";
import { z } from "zod";
import { analytics, readonlyPool } from "@/lib/db";

const SCHEMA_HINT = `
tickets(id text, queue text, status text, channel text, opened_at timestamptz, first_reply_at timestamptz)
csat(ticket_id text, score int, submitted_at timestamptz)
`;

const InsightQuery = z.object({
  sql: z.string().describe("One PostgreSQL SELECT statement over the tables above"),
  chart: z.enum(["bar", "line", "table"]),
});

export async function draftQuery(question: string) {
  const { object } = await generateObject({
    model: openai("gpt-4.1"),
    schema: InsightQuery,
    system: `Answer support-analytics questions with SQL over these tables only:${SCHEMA_HINT}`,
    prompt: question,
  });
  return object;
}

export async function runInsight(question: string) {
  const draft = await draftQuery(question);
  const { rows } = await readonlyPool.query(draft.sql);
  return { chart: draft.chart, rows };
}

export async function queueBacklog(question: string) {
  const { text: sort } = await generateText({
    model: openai("gpt-4.1-mini"),
    system: "Reply with a SQL ORDER BY expression for the tickets table that fits the question.",
    prompt: question,
  });
  const { text: queue } = await generateText({
    model: openai("gpt-4.1-mini"),
    system: "Reply with the queue name the question is about, nothing else.",
    prompt: question,
  });
  return analytics.execute(
    sql`SELECT id, status, opened_at FROM tickets WHERE queue = ${queue.trim()} AND status = 'open' ORDER BY ${sql.raw(sort)} LIMIT 50`,
  );
}

export async function channelVolume(question: string) {
  const { text: channel } = await generateText({
    model: openai("gpt-4.1-mini"),
    system: "Reply with one of: email, chat, phone.",
    prompt: question,
  });
  return analytics.execute(
    sql`SELECT date_trunc('day', opened_at) AS day, count(*) FROM tickets WHERE channel = ${channel.trim()} GROUP BY 1 ORDER BY 1`,
  );
}
