import { execSync } from "node:child_process";

import type { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";

import { clip, config } from "../config.js";

function curl(url: string, outFile: string): string {
  return execSync(`curl -sSL --max-time 20 -o ${outFile} -w "%{http_code}" ${url}`, {
    cwd: config.workspace,
  }).toString();
}

async function fetchText(url: string): Promise<string> {
  const host = new URL(url).hostname;
  if (!config.fetchAllowedHosts.includes(host)) {
    throw new Error(`Host ${host} is not on the fetch allowlist`);
  }
  const res = await fetch(url, { redirect: "error" });
  return clip(await res.text());
}

export function registerFetchTools(server: McpServer): void {
  server.registerTool(
    "download",
    {
      description: "Download a URL into the workspace downloads folder",
      inputSchema: z.object({ url: z.string().url(), name: z.string() }),
    },
    async ({ url, name }) => {
      const status = curl(url, `downloads/${name}`);
      return { content: [{ type: "text", text: `HTTP ${status}` }] };
    },
  );

  server.registerTool(
    "read_docs",
    { description: "Read a documentation page", inputSchema: z.object({ url: z.string().url() }) },
    async ({ url }) => ({ content: [{ type: "text", text: await fetchText(url) }] }),
  );
}
