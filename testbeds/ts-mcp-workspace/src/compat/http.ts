// The 1.x SDK over streamable HTTP, for the old desktop client that can only connect to a URL.
// Localhost only: the client runs on the same machine.
import { randomUUID } from "node:crypto";

import express from "express";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

import { config } from "../config.js";

const server = new McpServer({ name: "workspace-compat-http", version: "1.2.0" });

server.registerTool("workspace_info", { description: "Where the workspace checkout lives" }, async () => ({
  content: [{ type: "text", text: `workspace: ${config.workspace}` }],
}));

const transports = new Map<string, StreamableHTTPServerTransport>();

const app = express();
app.use(express.json());

app.post("/mcp", async (req, res) => {
  const sessionId = req.header("mcp-session-id");
  let transport = sessionId ? transports.get(sessionId) : undefined;
  if (!transport) {
    transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (id) => {
        transports.set(id, transport!);
      },
    });
    await server.connect(transport);
  }
  await transport.handleRequest(req, res, req.body);
});

app.listen(Number(process.env.WORKSPACE_COMPAT_PORT ?? 8788), "127.0.0.1");
