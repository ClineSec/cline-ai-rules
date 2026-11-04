// CommonJS server: require() imports and a handler declared after it is registered.
const { McpServer } = require("@modelcontextprotocol/sdk/server/mcp.js");
const childProcess = require("node:child_process");
const { exec: run } = require("child_process");
const { z } = require("zod");

const server = new McpServer({ name: "legacy-ops", version: "0.9.0" });

server.registerTool("archive", { inputSchema: { folder: z.string() } }, archiveFolder);

function archiveFolder({ folder }) {
  // ruleid: mcp-tool-arg-to-shell-ts
  childProcess.execSync("tar czf /tmp/archive.tgz " + folder);
  return { content: [{ type: "text", text: "ok" }] };
}

server.registerTool("open_url", { inputSchema: { url: z.string() } }, async ({ url }) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  run(`xdg-open ${url}`);
  return { content: [] };
});

server.registerTool("open_url_safe", { inputSchema: { url: z.string() } }, async ({ url }) => {
  // ok: mcp-tool-arg-to-shell-ts
  childProcess.execFileSync("xdg-open", [url]);
  return { content: [] };
});
