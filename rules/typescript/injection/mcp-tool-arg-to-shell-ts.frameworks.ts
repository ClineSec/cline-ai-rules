// Other ways to register a tool: the v1 SDK's low-level Server, punkpeye fastmcp, the Claude
// Agent SDK's in-process MCP tools, and named handlers; plus Bun Shell.
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { tool as sdkTool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
import { FastMCP } from "fastmcp";
import { execSync as sh, spawnSync } from "node:child_process";
import { $ } from "bun";
import { z } from "zod";

const low = new Server({ name: "ops", version: "2.0.0" }, { capabilities: { tools: {} } });

low.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  if (name === "lint") {
    // ruleid: mcp-tool-arg-to-shell-ts
    const out = sh(`eslint ${args?.path}`).toString();
    return { content: [{ type: "text", text: out }] };
  }
  return { content: [] };
});

low.setRequestHandler(ListToolsRequestSchema, async (request) => {
  // ok: mcp-tool-arg-to-shell-ts
  sh(`echo listing ${request.params?.cursor ?? ""}`);
  return { tools: [] };
});

const fm = new FastMCP({ name: "ops2", version: "1.0.0" });

fm.addTool({
  name: "which",
  parameters: z.object({ binary: z.string() }),
  execute: async (args) => {
    // ruleid: mcp-tool-arg-to-shell-ts
    return sh("which " + args.binary).toString();
  },
});

export const searchServer = createSdkMcpServer({
  name: "search",
  tools: [
    sdkTool("search_repo", "Search the repository", { query: z.string() }, async ({ query }) => {
      // ruleid: mcp-tool-arg-to-shell-ts
      const out = spawnSync("sh", ["-c", `rg --json ${query}`]).stdout.toString();
      return { content: [{ type: "text", text: out }] };
    }),
  ],
});

const checksum = async ({ path }: { path: string }) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  const text = await $`sha256sum ${{ raw: path }}`.text();
  return { content: [{ type: "text" as const, text }] };
};

low.setRequestHandler(CallToolRequestSchema, checksum);

fm.addTool({
  name: "uptime",
  parameters: z.object({ host: z.string() }),
  execute: async ({ host }) => {
    // ok: mcp-tool-arg-to-shell-ts
    return (await $`ssh ${host} uptime`.text()).trim();
  },
});

async function listResources(request: { params?: { cursor?: string } }) {
  // ok: mcp-tool-arg-to-shell-ts
  sh(`echo page ${request.params?.cursor ?? "0"}`);
  return { resources: [] };
}

low.setRequestHandler(ListToolsRequestSchema, listResources);
