// Streamable HTTP entrypoint, for MCP clients that can't spawn a stdio process. The browser
// IDE runs in its own container on the same Docker network and reaches this one by name.
import { createMcpExpressApp } from "@modelcontextprotocol/express";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
import { McpServer } from "@modelcontextprotocol/server";

import { registerBuildTools } from "./tools/build.js";
import { registerFetchTools } from "./tools/fetch.js";
import { registerGitTools } from "./tools/git.js";
import { registerSearchTools } from "./tools/search.js";

const HOST = process.env.WORKSPACE_HTTP_HOST ?? "0.0.0.0";
const PORT = Number(process.env.WORKSPACE_HTTP_PORT ?? 8787);

function createWorkspaceServer(): McpServer {
  const server = new McpServer({ name: "workspace", version: "1.2.0" });
  registerGitTools(server);
  registerSearchTools(server);
  registerBuildTools(server);
  registerFetchTools(server);
  return server;
}

// The IDE container calls us as http://workspace:8787, so that name has to pass the Host check.
const app = createMcpExpressApp({ host: HOST, allowedHosts: ["localhost", "workspace", "ide.example.com"] });

app.post("/mcp", async (req, res) => {
  // Stateless: a fresh server and transport per request.
  const server = createWorkspaceServer();
  const transport = new NodeStreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  res.on("close", () => {
    void transport.close();
    void server.close();
  });
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});

app.listen(PORT, HOST, () => {
  console.error(`workspace MCP listening on http://${HOST}:${PORT}/mcp`);
});
