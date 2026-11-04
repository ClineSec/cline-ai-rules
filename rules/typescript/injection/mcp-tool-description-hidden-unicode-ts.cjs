// A hand-written CommonJS MCP server (not strict code, so legacy octal escapes are allowed).
const { McpServer } = require("@modelcontextprotocol/sdk/server/mcp.js");

const server = new McpServer({ name: "hyphen-tools", version: "0.3.0" });

server.registerTool(
  "hyphenate",
  {
    // Three soft hyphens written as octal escapes:
    // ruleid: mcp-tool-description-hidden-unicode-ts
    description: "Hyph\255\255\255enate a word.",
    inputSchema: {}
  },
  async () => ({ content: [] })
);

server.registerTool(
  "compound",
  {
    // One octal soft hyphen, and \0255, which is U+0015 followed by "5":
    // ok: mcp-tool-description-hidden-unicode-ts
    description: "Donau\255dampfschiff; \0255\0255\0255 is not a soft hyphen.",
    inputSchema: {}
  },
  async () => ({ content: [] })
);

module.exports = { server };
