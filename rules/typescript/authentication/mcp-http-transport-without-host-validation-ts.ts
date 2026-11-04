// MCP TypeScript SDK 2.x transports on a bare Express app on localhost, with no Host or
// Origin check and no authentication anywhere in the file.
import { randomUUID } from "node:crypto";

import express from "express";
import { NodeStreamableHTTPServerTransport, toNodeHandler } from "@modelcontextprotocol/node";
import { createMcpHandler, McpServer, WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/server";

function buildServer(): McpServer {
  return new McpServer({ name: "notes", version: "1.0.0" });
}

const app = express();
app.use(express.json());

app.post("/mcp", async (req, res) => {
  // ruleid: mcp-http-transport-without-host-validation-ts
  const transport = new NodeStreamableHTTPServerTransport({ sessionIdGenerator: () => randomUUID() });
  await buildServer().connect(transport);
  await transport.handleRequest(req, res, req.body);
});

app.post("/mcp-legacy", async (req, res) => {
  // ruleid: mcp-http-transport-without-host-validation-ts
  const transport = new NodeStreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableDnsRebindingProtection: false,
  });
  await buildServer().connect(transport);
  await transport.handleRequest(req, res, req.body);
});

// The deprecated transport-level check, switched on with an allowlist.
app.post("/mcp-checked", async (req, res) => {
  // ok: mcp-http-transport-without-host-validation-ts
  const transport = new NodeStreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableDnsRebindingProtection: true,
    allowedHosts: ["127.0.0.1:3000", "localhost:3000"],
  });
  await buildServer().connect(transport);
  await transport.handleRequest(req, res, req.body);
});

// The 2.x per-request handler does no Host or Origin validation either.
// ruleid: mcp-http-transport-without-host-validation-ts
const handler = createMcpHandler(() => buildServer());
app.all("/mcp-modern", toNodeHandler(handler));

// A second listener for clients that speak fetch, on Bun.
Bun.serve({
  port: 3001,
  hostname: "127.0.0.1",
  async fetch(request: Request): Promise<Response> {
    // ruleid: mcp-http-transport-without-host-validation-ts
    const transport = new WebStandardStreamableHTTPServerTransport({ sessionIdGenerator: undefined });
    await buildServer().connect(transport);
    return transport.handleRequest(request);
  },
});

app.listen(3000, "127.0.0.1");
