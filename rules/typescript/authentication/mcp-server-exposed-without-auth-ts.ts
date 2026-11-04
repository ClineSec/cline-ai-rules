// MCP TypeScript SDK 2.x HTTP servers with no authentication anywhere in the file.
import { createMcpExpressApp } from "@modelcontextprotocol/express";
import { createMcpFastifyApp } from "@modelcontextprotocol/fastify";
import { createMcpHonoApp } from "@modelcontextprotocol/hono";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
import { McpServer } from "@modelcontextprotocol/server";
import { serve } from "@hono/node-server";

const PUBLIC_HOST = "0.0.0.0";

function buildServer(): McpServer {
  return new McpServer({ name: "notes", version: "1.0.0" });
}

// host: "0.0.0.0" switches off the helper's Host and Origin checks (only a console.warn).
// ruleid: mcp-server-exposed-without-auth-ts
const open = createMcpExpressApp({ host: "0.0.0.0" });
open.post("/mcp", async (req, res) => {
  const transport = new NodeStreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  await buildServer().connect(transport);
  await transport.handleRequest(req, res, req.body);
});
// Reported once, where the helper was given the host.
// ok: mcp-server-exposed-without-auth-ts
open.listen(3000, PUBLIC_HOST);

// allowedHosts stops DNS rebinding from a browser, but a direct client sets any Host header
// it likes, so this server is still open to the network.
// ruleid: mcp-server-exposed-without-auth-ts
const scoped = createMcpExpressApp({ host: "::", allowedHosts: ["notes.example.com"] });

// ruleid: mcp-server-exposed-without-auth-ts
const fromEnv = createMcpExpressApp({ host: process.env.NOTES_HOST ?? "0.0.0.0", jsonLimit: "1mb" });

// The host from a variable assigned earlier; the listen() on the same host is reported once.
const BIND = process.env.NOTES_BIND ?? "0.0.0.0";
// ruleid: mcp-server-exposed-without-auth-ts
const viaVar = createMcpExpressApp({ host: BIND });
// ok: mcp-server-exposed-without-auth-ts
viaVar.listen(3007, BIND);

// The helper keeps its localhost Host check, but listen() binds every interface, and a
// client that isn't a browser sends Host: localhost.
const local = createMcpExpressApp();
// ruleid: mcp-server-exposed-without-auth-ts
local.listen(3001, "0.0.0.0", () => console.log("listening"));

// ruleid: mcp-server-exposed-without-auth-ts
const fastify = createMcpFastifyApp({ host: "0.0.0.0" });
// ok: mcp-server-exposed-without-auth-ts
await fastify.listen({ port: 3002, host: "0.0.0.0" });

const hono = createMcpHonoApp();
// ruleid: mcp-server-exposed-without-auth-ts
serve({ fetch: hono.fetch, port: 3003, hostname: "0.0.0.0" });

// ok: mcp-server-exposed-without-auth-ts
const loopback = createMcpExpressApp();
// ok: mcp-server-exposed-without-auth-ts
loopback.listen(3004, "127.0.0.1");

// ok: mcp-server-exposed-without-auth-ts
const named = createMcpExpressApp({ host: "localhost" });
// Node's own default (no host) binds every interface too, but so does every web server
// that never chose a host; only an explicit all-interfaces bind is reported.
// ok: mcp-server-exposed-without-auth-ts
named.listen(3005);

// ok: mcp-server-exposed-without-auth-ts
await fastify.listen({ port: 3006, host: "127.0.0.1" });

// ok: mcp-server-exposed-without-auth-ts
if (process.env.NOTES_HOST === "0.0.0.0") console.warn("NOTES_HOST is a wildcard address");
