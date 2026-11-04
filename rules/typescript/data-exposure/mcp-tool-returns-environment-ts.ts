import { execFileSync, execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { McpServer, Server } from "@modelcontextprotocol/server";
import { tool } from "@anthropic-ai/claude-agent-sdk";
import dotenv from "dotenv";
import { z } from "zod";

const server = new McpServer({ name: "diagnostics", version: "1.0.0" });

server.registerTool("environment", { description: "Environment variables of the server" }, async () => {
  // ruleid: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: JSON.stringify(process.env, null, 2) }] };
});

// ruleid: mcp-tool-returns-environment-ts
server.registerTool("environment_structured", { description: "Environment as structured output" }, async () => ({
  content: [],
  structuredContent: { ...process.env },
}));

server.registerTool("environment_lines", {}, async () => {
  const lines = Object.entries(process.env).map(([key, value]) => `${key}=${value}`);
  // ruleid: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: lines.join("\n") }] };
});

server.registerTool(
  "read_variable",
  { inputSchema: z.object({ name: z.string() }) },
  async ({ name }) => {
    // ruleid: mcp-tool-returns-environment-ts
    return { content: [{ type: "text", text: process.env[name] ?? "" }] };
  },
);

server.registerTool("github_auth", {}, async () => {
  // ruleid: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: `token: ${process.env.GITHUB_TOKEN}` }] };
});

server.registerTool("printenv", {}, async () => {
  const out = execSync("printenv", { encoding: "utf8" });
  // ruleid: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: out }] };
});

server.registerTool("dotenv", {}, async () => {
  const loaded = dotenv.config({ path: ".env.local" });
  // ruleid: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: JSON.stringify(loaded.parsed) }] };
});

// ruleid: mcp-tool-returns-environment-ts
server.tool("legacy_environment", async () => ({
  content: [{ type: "text", text: JSON.stringify(Object.assign({}, process.env)) }],
}));

const procEnvironment = async () => {
  const raw = readFileSync("/proc/self/environ", "utf8");
  // ruleid: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: raw.split("\0").join("\n") }] };
};
server.registerTool("proc_environment", {}, procEnvironment);

const lowLevel = new Server({ name: "diagnostics-lowlevel", version: "1.0.0" }, { capabilities: { tools: {} } });
lowLevel.setRequestHandler("tools/call", async (request) => {
  if (request.params.name === "env") {
    // ruleid: mcp-tool-returns-environment-ts
    return { content: [{ type: "text", text: JSON.stringify(process.env) }] };
  }
  return { content: [{ type: "text", text: "unknown tool" }], isError: true };
});

// ruleid: mcp-tool-returns-environment-ts
export const envTool = tool("environment", "Environment of the agent host", {}, async () => ({
  content: [{ type: "text", text: JSON.stringify(process.env) }],
}));

// A prefix is not an allowlist: GITHUB_ keeps GITHUB_TOKEN, and masking AWS_ leaves the rest.
server.registerTool("github_settings", {}, async () => {
  const settings = Object.fromEntries(Object.entries(process.env).filter(([key]) => key.startsWith("GITHUB_")));
  // ruleid: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: JSON.stringify(settings) }] };
});

// An allowlist widened with a type assertion. A callback that starts with a parenthesized
// expression and a method call made OpenGrep 1.30.2 drop every finding in this file
// ("Invalid_argument: String.sub") before the filter sanitizers skipped such callbacks and
// matched this form on its own.
const SHOWN_KEYS = ["TZ", "LANG"] as const;

server.registerTool("shown_settings", {}, async () => {
  const settings = Object.fromEntries(Object.entries(process.env).filter(([key]) => (SHOWN_KEYS as readonly string[]).includes(key)));
  // ok: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: JSON.stringify(settings) }] };
});

server.registerTool("ci_variable", {}, async () => {
  const entry = Object.entries(process.env).find(([key]) => key.startsWith("CI_"));
  // ruleid: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: entry ? entry.join("=") : "" }] };
});

server.registerTool("masked_environment", {}, async () => {
  const masked = Object.entries(process.env).map(([key, value]) => [key, key.startsWith("AWS_") ? "***" : value]);
  // ruleid: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: JSON.stringify(Object.fromEntries(masked)) }] };
});

server.registerTool("environment_head", {}, async () => {
  // ruleid: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: JSON.stringify(process.env).slice(0, 4000) }] };
});

server.registerTool("encoded_environment", {}, async () => {
  // ruleid: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: Buffer.from(JSON.stringify(process.env)).toString("base64") }] };
});

// Near misses: named, non-secret settings, facts about secrets, and the environment handed to
// a child process rather than returned.

const SHOWN = new Set(["TZ", "LANG", "NODE_ENV"]);
const SECRET_NAME = /token|secret|passw|key|auth/i;

server.registerTool("shown_settings", {}, async () => {
  const settings = Object.fromEntries(Object.entries(process.env).filter(([key]) => SHOWN.has(key)));
  // ok: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: JSON.stringify(settings) }] };
});

server.registerTool("diag_settings", {}, async () => {
  const settings = Object.entries(process.env).filter(([key]) => key.startsWith("DIAG_") && !SECRET_NAME.test(key));
  // ok: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: JSON.stringify(Object.fromEntries(settings)) }] };
});

server.registerTool("safe_environment", {}, async () => {
  const masked = Object.entries(process.env).map(([key, value]) => [key, SECRET_NAME.test(key) ? "***" : value]);
  // ok: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: JSON.stringify(Object.fromEntries(masked)) }] };
});

server.registerTool("timezone_entry", {}, async () => {
  const entry = Object.entries(process.env).find(([key]) => key === "TZ");
  // ok: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: entry ? entry.join("=") : "" }] };
});

server.registerTool("token_preview", {}, async () => {
  const token = process.env.GITHUB_TOKEN ?? "";
  // ok: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: token ? `${token.slice(0, 4)}...` : "not set" }] };
});

server.registerTool("timezone", {}, async () => {
  const env = { ...process.env };
  // ok: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: `${env.TZ ?? "UTC"} ${process.env.LANG ?? "C"} ${process.env["NODE_ENV"]}` }] };
});

server.registerTool("credentials_status", {}, async () => ({
  // ok: mcp-tool-returns-environment-ts
  structuredContent: { github: "GITHUB_TOKEN" in process.env, openai: Boolean(process.env.OPENAI_API_KEY) },
  content: [],
}));

server.registerTool("variable_names", {}, async () => {
  // ok: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: Object.keys(process.env).sort().join("\n") }] };
});

server.registerTool("git_status", {}, async () => {
  const out = execFileSync("git", ["status", "--short"], { env: { ...process.env, GIT_PAGER: "cat" }, encoding: "utf8" });
  // ok: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: out }] };
});

server.registerTool(
  "read_allowed_variable",
  { inputSchema: z.object({ name: z.string() }) },
  async ({ name }) => {
    if (!SHOWN.has(name)) throw new Error(`not allowed: ${name}`);
    // ok: mcp-tool-returns-environment-ts
    return { content: [{ type: "text", text: process.env[name] ?? "" }] };
  },
);

server.registerTool(
  "echo",
  { inputSchema: z.object({ name: z.string() }) },
  async ({ name }) => {
    // ok: mcp-tool-returns-environment-ts
    return { content: [{ type: "text", text: `hello ${name}` }] };
  },
);

export function debugDump(): Record<string, string | undefined> {
  // ok: mcp-tool-returns-environment-ts
  return { ...process.env };
}

async function serverEnvironment() {
  // ruleid: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: JSON.stringify(process.env) }] };
}

server.registerTool("server_environment", { description: "Environment of the server process" }, serverEnvironment);

registerLate(server);

function registerLate(target: McpServer) {
  target.registerTool("late_environment", { description: "Environment, registered by a helper" }, lateEnvironment);
}

function lateEnvironment() {
  // ruleid: mcp-tool-returns-environment-ts
  return { content: [{ type: "text", text: JSON.stringify({ ...process.env }) }] };
}

// A filter callback that starts with a parenthesized fallback compared to a value. OpenGrep
// 1.30.2 aborted the whole file on it until the parenthesis guard covered operators.
function pendingJobs(jobs: { state?: string }[], wanted: string) {
  return jobs.filter((job) => (job.state ?? "queued") === wanted);
}

function firstPendingJob(jobs: { state?: string }[], wanted: string) {
  return jobs.find((job) => ((job.state ?? "queued") === wanted));
}
