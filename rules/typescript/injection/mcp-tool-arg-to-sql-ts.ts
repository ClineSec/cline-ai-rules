import { McpServer } from "@modelcontextprotocol/server";
import { PrismaClient } from "@prisma/client";
import Database from "better-sqlite3";
import { sql } from "drizzle-orm";
import { drizzle } from "drizzle-orm/node-postgres";
import knexFactory from "knex";
import { Pool } from "pg";
import { z } from "zod";

const server = new McpServer({ name: "inventory", version: "2.0.0" });
const pool = new Pool();
const prisma = new PrismaClient();
const local = new Database("inventory.db");
const knex = knexFactory({ client: "pg" });
const orm = drizzle(pool);

const SORT_COLUMNS: Record<string, string> = { sku: "sku", bin: "bin, sku" };
const ALLOWED_TABLES = new Set(["parts", "bins"]);

server.registerTool(
  "run_query",
  { description: "Run a read query", inputSchema: z.object({ query: z.string() }) },
  async ({ query }) => {
    // ruleid: mcp-tool-arg-to-sql-ts
    const { rows } = await pool.query(query);
    return { content: [{ type: "text", text: JSON.stringify(rows) }] };
  },
);

server.registerTool("find_part", { inputSchema: { name: z.string() } }, async (args) => {
  // ruleid: mcp-tool-arg-to-sql-ts
  const rows = local.prepare(`SELECT sku FROM parts WHERE name LIKE '%${args.name}%'`).all();
  return { content: [{ type: "text", text: JSON.stringify(rows) }] };
});

server.registerTool("parts_by", { inputSchema: { order: z.string() } }, async ({ order }) => {
  // ruleid: mcp-tool-arg-to-sql-ts
  const rows = await prisma.$queryRawUnsafe(`SELECT sku FROM "Part" ORDER BY ${order}`);
  return { content: [{ type: "text", text: JSON.stringify(rows) }] };
});

server.tool("bins_where", { filter: z.string() }, async ({ filter }) => {
  // ruleid: mcp-tool-arg-to-sql-ts
  const rows = await knex("bins").select("id").whereRaw(filter);
  return { content: [{ type: "text", text: JSON.stringify(rows) }] };
});

server.server.setRequestHandler("tools/call", async (request) => {
  // ruleid: mcp-tool-arg-to-sql-ts
  const { rows } = await pool.query({ text: String(request.params.arguments?.sql), rowMode: "array" });
  return { content: [{ type: "text", text: JSON.stringify(rows) }] };
});

// --- Near misses ---

server.registerTool("find_part_bound", { inputSchema: { name: z.string() } }, async ({ name }) => {
  // ok: mcp-tool-arg-to-sql-ts
  const { rows } = await pool.query("SELECT sku FROM parts WHERE name LIKE $1", [`%${name}%`]);
  return { content: [{ type: "text", text: JSON.stringify(rows) }] };
});

server.registerTool(
  "parts_sorted",
  { inputSchema: z.object({ order: z.enum(["sku", "bin"]), limit: z.number().int() }) },
  async ({ order, limit }) => {
    // ok: mcp-tool-arg-to-sql-ts
    const { rows } = await pool.query(`SELECT sku FROM parts ORDER BY ${order} LIMIT ${limit}`);
    return { content: [{ type: "text", text: JSON.stringify(rows) }] };
  },
);

server.registerTool("parts_lookup", { inputSchema: { order: z.string() } }, async ({ order }) => {
  // ok: mcp-tool-arg-to-sql-ts
  const { rows } = await pool.query(`SELECT sku FROM parts ORDER BY ${SORT_COLUMNS[order] ?? "sku"}`);
  return { content: [{ type: "text", text: JSON.stringify(rows) }] };
});

server.registerTool("table_size", { inputSchema: { table: z.string() } }, async ({ table }) => {
  if (!ALLOWED_TABLES.has(table)) throw new Error(`unknown table ${table}`);
  // ok: mcp-tool-arg-to-sql-ts
  const { rows } = await pool.query(`SELECT count(*) FROM ${table}`);
  return { content: [{ type: "text", text: JSON.stringify(rows) }] };
});

server.registerTool("bin_parts", { inputSchema: { bin: z.string() } }, async ({ bin }) => {
  // ok: mcp-tool-arg-to-sql-ts
  const rows = await orm.execute(sql`SELECT sku FROM parts WHERE bin = ${bin}`);
  return { content: [{ type: "text", text: JSON.stringify(rows) }] };
});

server.registerTool("bin_count", { inputSchema: { bin: z.string() } }, async ({ bin }) => {
  // ok: mcp-tool-arg-to-sql-ts
  const rows = await prisma.$queryRaw`SELECT count(*) FROM "Part" WHERE bin = ${bin}`;
  return { content: [{ type: "text", text: JSON.stringify(rows) }] };
});

async function queryParts(text: string, values: unknown[] = []) {
  const { rows } = await pool.query(text, values);
  return { content: [{ type: "text" as const, text: JSON.stringify(rows) }] };
}

server.registerTool("parts_where", { inputSchema: { condition: z.string() } }, async ({ condition }) =>
  // ruleid: mcp-tool-arg-to-sql-ts
  queryParts("SELECT sku, bin FROM parts WHERE " + condition),
);

server.registerTool("parts_named", { inputSchema: { name: z.string() } }, async ({ name }) =>
  // ok: mcp-tool-arg-to-sql-ts
  queryParts("SELECT sku, bin FROM parts WHERE name = $1", [name]),
);
