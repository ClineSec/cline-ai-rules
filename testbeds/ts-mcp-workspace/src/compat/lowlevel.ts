// The same tools for clients pinned to the 1.x SDK, on its low-level Server.
import { execFileSync, execSync } from "node:child_process";

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

import { clip, config } from "../config.js";

const TOOLS = [
  {
    name: "disk_usage",
    description: "Disk usage of a folder in the workspace",
    inputSchema: { type: "object", properties: { folder: { type: "string" } }, required: ["folder"] },
  },
  {
    name: "git_log",
    description: "One-line history for a ref",
    inputSchema: { type: "object", properties: { ref: { type: "string" } } },
  },
];

const server = new Server({ name: "workspace-compat", version: "1.2.0" }, { capabilities: { tools: {} } });

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const args = (request.params.arguments ?? {}) as Record<string, string>;
  switch (request.params.name) {
    case "disk_usage": {
      const out = execSync(`du -sh ${config.workspace}/${args.folder}`).toString();
      return { content: [{ type: "text", text: out }] };
    }
    case "git_log": {
      const out = execFileSync("git", ["log", "--oneline", "-n", "20", "--", args.ref ?? "HEAD"], {
        cwd: config.workspace,
      }).toString();
      return { content: [{ type: "text", text: clip(out) }] };
    }
    default:
      throw new Error(`Unknown tool: ${request.params.name}`);
  }
});

await server.connect(new StdioServerTransport());
