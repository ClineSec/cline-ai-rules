import { McpServer } from "@modelcontextprotocol/server";

const server = new McpServer({ name: "env-resources", version: "1.0.0" });

server.registerResource("env", "env://all", { mimeType: "application/json" }, async (uri) => {
  // ruleid: mcp-tool-returns-environment-ts
  return { contents: [{ uri: uri.href, text: JSON.stringify(process.env) }] };
});

server.registerPrompt("debug", { description: "Debug the server" }, () => {
  // ruleid: mcp-tool-returns-environment-ts
  return { messages: [{ role: "user", content: { type: "text", text: JSON.stringify(process.env) } }] };
});

server.registerResource("region", "env://region", {}, async (uri) => {
  // ok: mcp-tool-returns-environment-ts
  return { contents: [{ uri: uri.href, text: process.env.APP_REGION ?? "" }] };
});
