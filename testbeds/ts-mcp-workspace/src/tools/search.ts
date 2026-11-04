import { spawn } from "node:child_process";

import type { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";

import { clip, config } from "../config.js";

const searchInput = z.object({
  query: z.string().describe("Regular expression to search for"),
  glob: z.string().optional().describe("Only search files matching this glob"),
});

function collect(child: ReturnType<typeof spawn>): Promise<string> {
  return new Promise((resolve, reject) => {
    let out = "";
    child.stdout?.on("data", (chunk) => (out += chunk));
    child.on("error", reject);
    child.on("close", () => resolve(out));
  });
}

async function searchCode({ query, glob }: z.infer<typeof searchInput>) {
  const args = ["--line-number", "--max-count", "20"];
  if (glob) args.push("--glob", glob);
  const child = spawn("rg", [...args, query, config.workspace]);
  return { content: [{ type: "text" as const, text: clip(await collect(child)) }] };
}

async function searchLiteral({ query }: z.infer<typeof searchInput>) {
  const child = spawn("rg", ["--fixed-strings", "--line-number", "-e", query, "--", config.workspace]);
  return { content: [{ type: "text" as const, text: clip(await collect(child)) }] };
}

export function registerSearchTools(server: McpServer): void {
  server.registerTool("search_code", { description: "Search the workspace", inputSchema: searchInput }, searchCode);
  server.registerTool(
    "search_literal",
    { description: "Search the workspace for a fixed string", inputSchema: searchInput },
    searchLiteral,
  );
}
