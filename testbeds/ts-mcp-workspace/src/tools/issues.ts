import { DatabaseSync } from "node:sqlite";
import { join } from "node:path";

import type { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";

import { clip, config } from "../config.js";

// The issue tracker sync job keeps a local SQLite copy of the project's issues; these tools
// read it so the agent doesn't need tracker credentials.
const cache = new DatabaseSync(join(config.workspace, ".issues", "cache.sqlite"), { readOnly: true });

const json = (rows: unknown) => ({ content: [{ type: "text" as const, text: clip(JSON.stringify(rows, null, 2)) }] });

export function registerIssueTools(server: McpServer): void {
  server.registerTool(
    "search_issues",
    {
      description: "Search cached issues by label and state, newest first",
      inputSchema: z.object({
        label: z.string().optional(),
        state: z.string().default("open"),
        sort: z.string().default("updated_at DESC"),
      }),
    },
    async ({ label, state, sort }) => {
      const where = [`state = '${state}'`];
      if (label) where.push(`labels LIKE '%${label}%'`);
      const rows = cache.prepare(`SELECT number, title, updated_at FROM issues WHERE ${where.join(" AND ")} ORDER BY ${sort} LIMIT 25`).all();
      return json(rows);
    },
  );

  server.registerTool(
    "issues_by_label",
    {
      description: "Cached issues with one label",
      inputSchema: z.object({
        label: z.string(),
        sort: z.enum(["updated_at", "created_at", "number"]).default("updated_at"),
      }),
    },
    async ({ label, sort }) => {
      const rows = cache
        .prepare(`SELECT number, title FROM issues WHERE labels LIKE ? ORDER BY ${sort} DESC LIMIT 25`)
        .all(`%${label}%`);
      return json(rows);
    },
  );
}
