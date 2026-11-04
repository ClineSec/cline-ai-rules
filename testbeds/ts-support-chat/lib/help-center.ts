import { openai } from "@ai-sdk/openai";
import { embed } from "ai";
import { cosineDistance, desc, gt, sql } from "drizzle-orm";
import { pgTable, text, vector } from "drizzle-orm/pg-core";
import { analytics } from "./db";

// Help-center articles, embedded nightly from the CMS export. Customers can comment on
// articles, and the comments are indexed with them.
export const helpArticles = pgTable("help_articles", {
  slug: text("slug").primaryKey(),
  title: text("title").notNull(),
  content: text("content").notNull(),
  embedding: vector("embedding", { dimensions: 1536 }).notNull(),
});

const LINK_BUDGET = 6_000;

export async function findRelevantArticles(question: string, limit = 4) {
  const { embedding } = await embed({ model: openai.embedding("text-embedding-3-small"), value: question });
  const similarity = sql<number>`1 - (${cosineDistance(helpArticles.embedding, embedding)})`;
  return analytics
    .select({ slug: helpArticles.slug, title: helpArticles.title, content: helpArticles.content, similarity })
    .from(helpArticles)
    .where(gt(similarity, 0.5))
    .orderBy(desc(similarity))
    .limit(limit);
}

/** The page behind a link the customer pasted into the chat, as plain text. */
export async function fetchSharedLink(url: string): Promise<string> {
  const res = await fetch(url, { redirect: "follow", signal: AbortSignal.timeout(8_000) });
  if (!res.ok) return "";
  const html = await res.text();
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .slice(0, LINK_BUDGET);
}
