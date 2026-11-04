// MCP TypeScript SDK 1.x transports on a bare Express app, no Host check, no auth.
const express = require("express");
const { McpServer } = require("@modelcontextprotocol/sdk/server/mcp.js");
const { StreamableHTTPServerTransport } = require("@modelcontextprotocol/sdk/server/streamableHttp.js");
const { SSEServerTransport } = require("@modelcontextprotocol/sdk/server/sse.js");

const server = new McpServer({ name: "notes", version: "1.0.0" });
const app = express();
app.use(express.json());
const sessions = {};

app.post("/mcp", async (req, res) => {
  // ruleid: mcp-http-transport-without-host-validation-ts
  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});

app.get("/sse", async (_req, res) => {
  // ruleid: mcp-http-transport-without-host-validation-ts
  const transport = new SSEServerTransport("/messages", res);
  sessions[transport.sessionId] = transport;
  await server.connect(transport);
});

app.get("/sse-checked", async (_req, res) => {
  // ok: mcp-http-transport-without-host-validation-ts
  const transport = new SSEServerTransport("/messages", res, {
    enableDnsRebindingProtection: true,
    allowedHosts: ["localhost:3000"],
  });
  await server.connect(transport);
});

app.listen(3000);
