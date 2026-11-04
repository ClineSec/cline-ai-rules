import Anthropic from "@anthropic-ai/sdk";
import { PrismaClient } from "@prisma/client";
import { generateObject, generateText } from "ai";
import Database from "better-sqlite3";
import { sql } from "drizzle-orm";
import { drizzle } from "drizzle-orm/node-postgres";
import knexFactory from "knex";
import mysql from "mysql2/promise";
import OpenAI from "openai";
import { Pool } from "pg";
import postgres from "postgres";
import { Sequelize, QueryTypes } from "sequelize";
import { z } from "zod";

const openai = new OpenAI();
const anthropic = new Anthropic();
const pool = new Pool();
const prisma = new PrismaClient();
const knex = knexFactory({ client: "pg" });
const sequelize = new Sequelize("postgres://reports@db.invalid/reports");
const pg = postgres("postgres://reports@db.invalid/reports");
const orm = drizzle(pool);
const local = new Database("reports.db");

const SORT_COLUMNS: Record<string, string> = { newest: "created_at DESC", oldest: "created_at ASC" };
const ALLOWED_TABLES = new Set(["tickets", "queues"]);

export async function answerWithPg(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ruleid: llm-output-to-sql-ts
  return (await pool.query(text)).rows;
}

export async function answerWithClient(question: string) {
  const resp = await openai.chat.completions.create({
    model: "gpt-5",
    messages: [{ role: "user", content: question }],
  });
  const column = resp.choices[0].message.content ?? "id";
  const client = await pool.connect();
  try {
    // ruleid: llm-output-to-sql-ts
    return (await client.query(`SELECT id, ${column} FROM tickets LIMIT 20`)).rows;
  } finally {
    client.release();
  }
}

export async function answerWithMysql(question: string) {
  const conn = await mysql.createConnection({ host: "db.invalid" });
  const msg = await anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 512,
    messages: [{ role: "user", content: question }],
  });
  const block = msg.content[0];
  const statement = block.type === "text" ? block.text : "";
  // ruleid: llm-output-to-sql-ts
  const [rows] = await conn.execute(statement);
  return rows;
}

export async function answerWithSqlite(question: string) {
  const { object } = await generateObject({
    model: "openai/gpt-5",
    schema: z.object({ sql: z.string() }),
    prompt: question,
  });
  // ruleid: llm-output-to-sql-ts
  return local.prepare(object.sql).all();
}

export async function answerWithPrisma(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ruleid: llm-output-to-sql-ts
  return prisma.$queryRawUnsafe(text);
}

export async function answerWithKnex(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ruleid: llm-output-to-sql-ts
  return knex("tickets").select("id").whereRaw(text);
}

export async function answerWithSequelize(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ruleid: llm-output-to-sql-ts
  return sequelize.query(text, { type: QueryTypes.SELECT });
}

export async function sortWithDrizzleRaw(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ruleid: llm-output-to-sql-ts
  return orm.execute(sql`SELECT id FROM tickets ORDER BY ${sql.raw(text)}`);
}

export async function answerWithPostgresJs(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ruleid: llm-output-to-sql-ts
  return pg.unsafe(text);
}

export async function answerWithQueryConfig(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ruleid: llm-output-to-sql-ts
  return pool.query({ text, rowMode: "array" });
}

// --- near misses ---------------------------------------------------------------------

export async function boundParameter(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ok: llm-output-to-sql-ts
  return (await pool.query("SELECT id FROM tickets WHERE queue = $1", [text.trim()])).rows;
}

export async function boundParameterConfig(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ok: llm-output-to-sql-ts
  return pool.query({ text: "SELECT id FROM tickets WHERE queue = $1", values: [text.trim()] });
}

export async function prismaTagged(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ok: llm-output-to-sql-ts
  return prisma.$queryRaw`SELECT id FROM tickets WHERE title ILIKE ${"%" + text + "%"}`;
}

export async function drizzleTemplate(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ok: llm-output-to-sql-ts
  return orm.execute(sql`SELECT id FROM tickets WHERE queue = ${text}`);
}

export async function mysqlFormat(question: string) {
  const conn = await mysql.createConnection({ host: "db.invalid" });
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  const statement = mysql.format("SELECT id FROM tickets WHERE queue = ?", [text]);
  // ok: llm-output-to-sql-ts
  return conn.query(statement);
}

export async function allowlistedSort(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  const order = SORT_COLUMNS[text.trim()] ?? "created_at DESC";
  // ok: llm-output-to-sql-ts
  return pool.query(`SELECT id FROM tickets ORDER BY ${order} LIMIT 20`);
}

export async function checkedTable(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  const table = text.trim();
  if (!ALLOWED_TABLES.has(table)) throw new Error(`unknown table ${table}`);
  // ok: llm-output-to-sql-ts
  return pool.query(`SELECT count(*) FROM ${table}`);
}

export async function numericLimit(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ok: llm-output-to-sql-ts
  return pool.query(`SELECT id FROM tickets LIMIT ${Number(text)}`);
}

export async function queryBuilder(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ok: llm-output-to-sql-ts
  return knex("tickets").where({ queue: text.trim() }).select("id");
}

export async function regexInDbFile(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  const ticketRef = /TCK-(\d+)/;
  // ok: llm-output-to-sql-ts
  return ticketRef.exec(text);
}

export async function storeAnswer(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ok: llm-output-to-sql-ts
  local.prepare("INSERT INTO answers (question, answer) VALUES (?, ?)").run(question, text);
}

async function fetchReport(text: string, values: unknown[] = []) {
  const { rows } = await pool.query(text, values);
  return rows;
}

export async function ticketsByModelSort(question: string) {
  const { text: order } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ruleid: llm-output-to-sql-ts
  return fetchReport(`SELECT id, status FROM tickets ORDER BY ${order} LIMIT 50`);
}

export async function ticketsByNamedSort(question: string) {
  const { text } = await generateText({ model: "openai/gpt-5", prompt: question });
  // ok: llm-output-to-sql-ts
  console.info(`SELECT plan for ${text} FROM the planner`);
  // ok: llm-output-to-sql-ts
  return fetchReport("SELECT id, status FROM tickets WHERE title = $1", [text]);
}

// The text block picked out of the content array with find() (assigned form).
export async function firstTextBlock(question: string) {
  const msg = await anthropic.messages.create({
    model: "claude-sonnet-4-5",
    max_tokens: 512,
    messages: [{ role: "user", content: question }],
  });
  const block = msg.content.find((b) => b.type === "text");
  // ruleid: llm-output-to-sql-ts
  return (await pool.query(block?.type === "text" ? block.text : "")).rows;
}
