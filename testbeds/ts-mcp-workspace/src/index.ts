#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/server";
import { StdioServerTransport } from "@modelcontextprotocol/server/stdio";

import { registerBuildTools } from "./tools/build.js";
import { registerDiagnosticTools } from "./tools/diagnostics.js";
import { registerFetchTools } from "./tools/fetch.js";
import { registerGitTools } from "./tools/git.js";
import { registerIssueTools } from "./tools/issues.js";
import { registerSearchTools } from "./tools/search.js";
import { registerSnippetTools } from "./tools/snippets.js";

export function createServer(): McpServer {
  const server = new McpServer(
    { name: "workspace", version: "1.2.0" },
    { instructions: "Tools for the project checkout. Prefer search_code before reading whole files." },
  );
  registerGitTools(server);
  registerSearchTools(server);
  registerBuildTools(server);
  registerFetchTools(server);
  registerSnippetTools(server);
  registerIssueTools(server);
  registerDiagnosticTools(server);
  return server;
}

const transport = new StdioServerTransport();
await createServer().connect(transport);
