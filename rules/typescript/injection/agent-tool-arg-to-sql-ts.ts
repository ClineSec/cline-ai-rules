import { tool } from "ai";
import { tool as agentTool } from "@openai/agents";
import { tool as lcTool, DynamicStructuredTool, StructuredTool } from "@langchain/core/tools";
import mysql from "mysql2/promise";
import { Pool } from "pg";
import postgres from "postgres";
import { Sequelize } from "sequelize";
import { z } from "zod";

const pool = new Pool();
const sequelize = new Sequelize("postgres://crm@db.invalid/crm");
const pg = postgres("postgres://crm@db.invalid/crm");
const REGION_ORDER: Record<string, string> = { name: "name", revenue: "revenue DESC" };

// --- Vercel AI SDK ---------------------------------------------------------------------------

export const accountLookup = tool({
  description: "Find accounts by name.",
  inputSchema: z.object({ name: z.string() }),
  execute: async ({ name }) => {
    // ruleid: agent-tool-arg-to-sql-ts
    const { rows } = await pool.query("SELECT id FROM accounts WHERE name = '" + name + "'");
    return rows;
  },
});

export const accountsSorted = tool({
  description: "List accounts in a sort order.",
  inputSchema: z.object({ order: z.enum(["name", "revenue"]), limit: z.number().int() }),
  execute: async ({ order, limit }) => {
    // ok: agent-tool-arg-to-sql-ts
    const { rows } = await pool.query(`SELECT id FROM accounts ORDER BY ${REGION_ORDER[order]} LIMIT ${limit}`);
    return rows;
  },
});

// --- OpenAI Agents JS ------------------------------------------------------------------------

export const regionAccounts = agentTool({
  name: "region_accounts",
  description: "Accounts in a region.",
  parameters: z.object({ region: z.string() }),
  async execute(input) {
    const conn = await mysql.createConnection({ host: "db.invalid" });
    // ruleid: agent-tool-arg-to-sql-ts
    const [rows] = await conn.query(`SELECT id FROM accounts WHERE region = '${input.region}'`);
    return JSON.stringify(rows);
  },
});

export const regionAccountsBound = agentTool({
  name: "region_accounts_bound",
  description: "Accounts in a region.",
  parameters: z.object({ region: z.string() }),
  async execute(input) {
    const conn = await mysql.createConnection({ host: "db.invalid" });
    // ok: agent-tool-arg-to-sql-ts
    const [rows] = await conn.execute("SELECT id FROM accounts WHERE region = ?", [input.region]);
    return JSON.stringify(rows);
  },
});

// --- LangChain.js ----------------------------------------------------------------------------

export const runSql = lcTool(
  async ({ query }) => {
    // ruleid: agent-tool-arg-to-sql-ts
    return JSON.stringify(await sequelize.query(query));
  },
  { name: "run_sql", description: "Run SQL.", schema: z.object({ query: z.string() }) },
);

export const churned = new DynamicStructuredTool({
  name: "churned",
  description: "Accounts churned since a day.",
  schema: z.object({ day: z.string() }),
  // ruleid: agent-tool-arg-to-sql-ts
  func: async ({ day }) => JSON.stringify(await pg.unsafe(`SELECT id FROM accounts WHERE churned_at > '${day}'`)),
});

export const churnedBound = new DynamicStructuredTool({
  name: "churned_bound",
  description: "Accounts churned since a day.",
  schema: z.object({ day: z.string() }),
  // ok: agent-tool-arg-to-sql-ts
  func: async ({ day }) => JSON.stringify(await pg`SELECT id FROM accounts WHERE churned_at > ${day}`),
});

class NotesTool extends StructuredTool {
  name = "notes";
  description = "Notes for an account.";
  schema = z.object({ accountId: z.string() });

  async _call({ accountId }: { accountId: string }) {
    // ruleid: agent-tool-arg-to-sql-ts
    const { rows } = await pool.query(`SELECT body FROM notes WHERE account_id = ${accountId}`);
    return JSON.stringify(rows);
  }

  async byNumber({ accountId }: { accountId: string }) {
    // ok: agent-tool-arg-to-sql-ts
    const { rows } = await pool.query(`SELECT body FROM notes WHERE account_id = ${Number(accountId)}`);
    return JSON.stringify(rows);
  }
}

export const notes = new NotesTool();
