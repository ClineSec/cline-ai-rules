// createMcpExpressApp() defaults to host '127.0.0.1', which adds the localhost Host and
// Origin checks in front of every route.
import { createMcpExpressApp } from "@modelcontextprotocol/express";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
import { McpServer } from "@modelcontextprotocol/server";

const app = createMcpExpressApp();
app.post("/mcp", async (req, res) => {
  const server = new McpServer({ name: "notes", version: "1.0.0" });
  // ok: mcp-http-transport-without-host-validation-ts
  const transport = new NodeStreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});
app.listen(3000, "127.0.0.1");
