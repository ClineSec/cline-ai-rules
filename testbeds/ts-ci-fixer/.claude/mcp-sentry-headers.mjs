// headersHelper for the Sentry MCP server in .mcp.json. Claude Code strips credential
// variables from a project helper's environment, so the token comes from a file.
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const token = readFileSync(join(homedir(), ".config", "ci-fixer", "sentry-mcp-token"), "utf8").trim();
process.stdout.write(JSON.stringify({ Authorization: `Bearer ${token}` }));
