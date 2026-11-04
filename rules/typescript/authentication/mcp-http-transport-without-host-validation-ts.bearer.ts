// A web page can't attach a bearer token through DNS rebinding, so an authenticated
// endpoint doesn't need the Host check to be safe from it.
import express from "express";
import { requireBearerAuth } from "@modelcontextprotocol/express";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
import { McpServer } from "@modelcontextprotocol/server";

import { verifier } from "./verifier.js";

const app = express();
app.use(express.json());
app.post("/mcp", requireBearerAuth({ verifier }), async (req, res) => {
  const server = new McpServer({ name: "notes", version: "1.0.0" });
  // ok: mcp-http-transport-without-host-validation-ts
  const transport = new NodeStreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});
app.listen(3000, "127.0.0.1");
