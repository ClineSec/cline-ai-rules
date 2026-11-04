// MCP TypeScript SDK 1.x on a bare Express app, and punkpeye fastmcp, with no authentication.
const express = require("express");
const { randomUUID } = require("node:crypto");
const { McpServer } = require("@modelcontextprotocol/sdk/server/mcp.js");
const { StreamableHTTPServerTransport } = require("@modelcontextprotocol/sdk/server/streamableHttp.js");
const { createMcpExpressApp } = require("@modelcontextprotocol/sdk/server/express.js");
const { FastMCP } = require("fastmcp");

const app = express();
app.use(express.json());
app.post("/mcp", async (req, res) => {
  const server = new McpServer({ name: "notes", version: "1.0.0" });
  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: () => randomUUID() });
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});
// ruleid: mcp-server-exposed-without-auth-ts
app.listen(Number(process.env.PORT || 3000), "0.0.0.0");

// ruleid: mcp-server-exposed-without-auth-ts
const legacy = createMcpExpressApp({ host: "0.0.0.0" });

const notes = new FastMCP({ name: "notes", version: "1.0.0" });
// ruleid: mcp-server-exposed-without-auth-ts
notes.start({ transportType: "httpStream", httpStream: { port: 8080, host: "0.0.0.0" } });

// ok: mcp-server-exposed-without-auth-ts
notes.start({ transportType: "httpStream", httpStream: { port: 8081 } });
