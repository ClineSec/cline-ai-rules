import { McpServer, ResourceTemplate } from "@modelcontextprotocol/server";
import { Pool } from "pg";
import { z } from "zod";

const server = new McpServer({ name: "catalog", version: "1.0.0" });
const pool = new Pool();

server.registerResource("table-schema", new ResourceTemplate("table://{name}/schema", { list: undefined }), {}, async (uri, { name }) => {
  // ruleid: mcp-tool-arg-to-sql-ts
  const { rows } = await pool.query(`SELECT column_name FROM information_schema.columns WHERE table_name = '${name}'`);
  return { contents: [{ uri: uri.href, text: JSON.stringify(rows) }] };
});

server.registerPrompt("orders", { argsSchema: z.object({ customer: z.string() }) }, async ({ customer }) => {
  // ruleid: mcp-tool-arg-to-sql-ts
  const { rows } = await pool.query("SELECT id, total FROM orders WHERE customer = '" + customer + "'");
  return { messages: [{ role: "user", content: { type: "text", text: JSON.stringify(rows) } }] };
});

server.registerPrompt("orders_safe", { argsSchema: z.object({ customer: z.string() }) }, async ({ customer }) => {
  // ok: mcp-tool-arg-to-sql-ts
  const { rows } = await pool.query("SELECT id, total FROM orders WHERE customer = $1", [customer]);
  return { messages: [{ role: "user", content: { type: "text", text: JSON.stringify(rows) } }] };
});
