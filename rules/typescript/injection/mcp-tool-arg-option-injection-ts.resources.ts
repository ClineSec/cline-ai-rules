import { McpServer, ResourceTemplate } from "@modelcontextprotocol/server";
import { execFileSync } from "node:child_process";
import { z } from "zod";

const server = new McpServer({ name: "git-resources", version: "1.0.0" });

server.registerResource("diff", new ResourceTemplate("git://diff/{ref}", { list: undefined }), {}, async (uri, { ref }) => {
  // ruleid: mcp-tool-arg-option-injection-ts
  const text = execFileSync("git", ["diff", String(ref)], { cwd: "/srv/checkout" }).toString();
  return { contents: [{ uri: uri.href, text }] };
});

server.registerPrompt("review_branch", { argsSchema: z.object({ branch: z.string() }) }, ({ branch }) => {
  // ruleid: mcp-tool-arg-option-injection-ts
  const log = execFileSync("git", ["log", "--oneline", branch], { cwd: "/srv/checkout" }).toString();
  return { messages: [{ role: "user", content: { type: "text", text: log } }] };
});

server.registerPrompt("review_branch_safe", { argsSchema: z.object({ branch: z.string() }) }, ({ branch }) => {
  // ok: mcp-tool-arg-option-injection-ts
  const log = execFileSync("git", ["log", "--oneline", "--end-of-options", branch], { cwd: "/srv/checkout" }).toString();
  return { messages: [{ role: "user", content: { type: "text", text: log } }] };
});
