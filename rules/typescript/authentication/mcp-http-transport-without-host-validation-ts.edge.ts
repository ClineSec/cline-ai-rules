// A Cloudflare Worker: the platform routes by hostname, so DNS rebinding can't reach it.
import { McpServer, WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/server";

export default {
  async fetch(request: Request): Promise<Response> {
    const server = new McpServer({ name: "notes", version: "1.0.0" });
    // ok: mcp-http-transport-without-host-validation-ts
    const transport = new WebStandardStreamableHTTPServerTransport({ sessionIdGenerator: undefined });
    await server.connect(transport);
    return transport.handleRequest(request);
  },
};
