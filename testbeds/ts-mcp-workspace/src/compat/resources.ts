// Workspace files as resources for clients pinned to the 1.x SDK, on its low-level Server.
import { execSync } from "node:child_process";
import { readdirSync } from "node:fs";

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { ListResourcesRequestSchema, ReadResourceRequestSchema } from "@modelcontextprotocol/sdk/types.js";

import { clip, config } from "../config.js";

const server = new Server({ name: "workspace-compat-resources", version: "1.2.0" }, { capabilities: { resources: {} } });

server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: readdirSync(config.workspace).map((name) => ({ uri: `workspace://head/${name}`, name })),
}));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const file = request.params.uri.replace("workspace://head/", "");
  const text = execSync(`git show HEAD:${file}`, { cwd: config.workspace }).toString();
  return { contents: [{ uri: request.params.uri, mimeType: "text/plain", text: clip(text) }] };
});

await server.connect(new StdioServerTransport());
