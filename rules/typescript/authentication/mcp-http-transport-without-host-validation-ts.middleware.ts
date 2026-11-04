// A bare Express app with the SDK's Host-header middleware mounted by hand.
import express from "express";
import { hostHeaderValidation } from "@modelcontextprotocol/express";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
import { McpServer } from "@modelcontextprotocol/server";

const app = express();
app.use(hostHeaderValidation(["localhost", "127.0.0.1"]));
app.use(express.json());
app.post("/mcp", async (req, res) => {
  const server = new McpServer({ name: "notes", version: "1.0.0" });
  // ok: mcp-http-transport-without-host-validation-ts
  const transport = new NodeStreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});
app.listen(3000, "127.0.0.1");
