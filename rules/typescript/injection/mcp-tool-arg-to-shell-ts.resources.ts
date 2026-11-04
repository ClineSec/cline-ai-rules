// Resource templates and prompts: the client fills a template's variables and a prompt's
// arguments, and clients let the model choose them, so they're sources like tool arguments.
import { McpServer, ResourceTemplate } from "@modelcontextprotocol/server";
import { McpServer as LegacyMcpServer, ResourceTemplate as LegacyTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  GetPromptRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { FastMCP } from "fastmcp";
import { execSync } from "node:child_process";
import { z } from "zod";

const server = new McpServer({ name: "logs", version: "2.0.0" });
const legacy = new LegacyMcpServer({ name: "logs-legacy", version: "1.0.0" });
const low = new Server({ name: "logs-low", version: "1.0.0" }, { capabilities: { resources: {}, prompts: {} } });
const fm = new FastMCP({ name: "runbooks", version: "1.0.0" });

server.registerResource(
  "unit-logs",
  new ResourceTemplate("logs://{service}/tail", { list: undefined }),
  { mimeType: "text/plain" },
  async (uri, { service }) => {
    // ruleid: mcp-tool-arg-to-shell-ts
    const text = execSync(`journalctl -u ${service} -n 50`).toString();
    return { contents: [{ uri: uri.href, text }] };
  },
);

const remote = new ResourceTemplate("mirror://{+path}", { list: undefined });
server.registerResource("mirror", remote, {}, async (uri) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  const text = execSync("curl -s " + uri.href).toString();
  return { contents: [{ uri: uri.href, text }] };
});

server.registerPrompt(
  "triage",
  { description: "Triage a failing unit", argsSchema: z.object({ unit: z.string() }) },
  ({ unit }) => {
    // ruleid: mcp-tool-arg-to-shell-ts
    const status = execSync("systemctl status " + unit).toString();
    return { messages: [{ role: "user", content: { type: "text", text: status } }] };
  },
);

legacy.prompt("explain_unit", { unit: z.string() }, ({ unit }) => ({
  // ruleid: mcp-tool-arg-to-shell-ts
  messages: [{ role: "user", content: { type: "text", text: execSync(`systemctl cat ${unit}`).toString() } }],
}));

legacy.prompt("disk_report", "Disk usage of a mount", { mount: z.string() }, async (args) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  const text = execSync("df -h " + args.mount).toString();
  return { messages: [{ role: "user", content: { type: "text", text } }] };
});

legacy.resource("runbook", new LegacyTemplate("runbook://{name}", { list: undefined }), async (uri, variables) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  const text = execSync(`cat /srv/runbooks/${variables.name}.md`).toString();
  return { contents: [{ uri: uri.href, text }] };
});

low.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  const text = execSync(`cat ${request.params.uri.replace("file://", "")}`).toString();
  return { contents: [{ uri: request.params.uri, text }] };
});

low.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const unit = request.params.arguments?.unit ?? "";
  // ruleid: mcp-tool-arg-to-shell-ts
  const text = execSync("systemctl is-active " + unit).toString();
  return { messages: [{ role: "user", content: { type: "text", text } }] };
});

async function readDeps(uri: URL, { unit }: { unit?: string | string[] }): Promise<{ contents: { uri: string; text: string }[] }> {
  // ruleid: mcp-tool-arg-to-shell-ts
  const text = execSync(`systemctl list-dependencies ${unit}`).toString();
  return { contents: [{ uri: uri.href, text }] };
}

const explainEnv = async ({ unit }: { unit: string }) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  const text = execSync(`systemctl show ${unit} -p Environment`).toString();
  return { messages: [{ role: "user" as const, content: { type: "text" as const, text } }] };
};

server.registerResource("deps", new ResourceTemplate("deps://{unit}", { list: undefined }), {}, readDeps);
server.registerPrompt("explain_env", { argsSchema: z.object({ unit: z.string() }) }, explainEnv);

server.registerPrompt("restart_plan", { argsSchema: z.object({ unit: z.string() }) }, restartPlan);

function restartPlan({ unit }: { unit: string }) {
  // ruleid: mcp-tool-arg-to-shell-ts
  const text = execSync("systemctl list-dependencies --reverse " + unit).toString();
  return { messages: [{ role: "user" as const, content: { type: "text" as const, text } }] };
}

// Registered inside a factory function, declared after it at module level.
export function registerUnitPrompts(srv: McpServer) {
  srv.registerPrompt("unit_show", { argsSchema: z.object({ unit: z.string() }) }, unitShow);
  srv.registerTool("unit_cat", { inputSchema: { unit: z.string() } }, unitCat);
  srv.registerResource("unit_file", new ResourceTemplate("unit://{name}", { list: undefined }), {}, unitFile);
}

function unitShow({ unit }: { unit: string }) {
  // ruleid: mcp-tool-arg-to-shell-ts
  const text = execSync("systemctl show " + unit).toString();
  return { messages: [{ role: "user" as const, content: { type: "text" as const, text } }] };
}

const unitCat = async ({ unit }: { unit: string }) => {
  // ruleid: mcp-tool-arg-to-shell-ts
  return { content: [{ type: "text" as const, text: execSync(`systemctl cat ${unit}`).toString() }] };
};

function unitFile(uri: URL, { name }: { name?: string | string[] }) {
  // ruleid: mcp-tool-arg-to-shell-ts
  const text = execSync(`systemctl cat ${name}`).toString();
  return { contents: [{ uri: uri.href, text }] };
}

fm.addResourceTemplate({
  uriTemplate: "file:///logs/{name}.log",
  name: "Application logs",
  mimeType: "text/plain",
  arguments: [{ name: "name", description: "Log name", required: true }],
  load: async ({ name }) => {
    // ruleid: mcp-tool-arg-to-shell-ts
    return { text: execSync(`tail -n 100 /var/log/${name}.log`).toString() };
  },
});

fm.addPrompt({
  name: "summarize-unit",
  arguments: [{ name: "unit", required: true }],
  load: async (args) => {
    // ruleid: mcp-tool-arg-to-shell-ts
    return `Summarize:\n${execSync("journalctl -u " + args.unit + " -n 30").toString()}`;
  },
});

// --- Near misses ---

server.registerResource("summary", "logs://system/summary", { mimeType: "text/plain" }, async (uri) => {
  // ok: mcp-tool-arg-to-shell-ts
  const text = execSync("journalctl -n 20 && echo " + uri.href).toString();
  return { contents: [{ uri: uri.href, text }] };
});

server.registerPrompt("uptime", { description: "Uptime report" }, (ctx) => {
  // ok: mcp-tool-arg-to-shell-ts
  const text = execSync("uptime").toString() + String(ctx.sessionId);
  return { messages: [{ role: "user", content: { type: "text", text } }] };
});

server.registerPrompt(
  "level_report",
  { argsSchema: z.object({ level: z.enum(["info", "warning", "err"]) }) },
  ({ level }) => {
    // ok: mcp-tool-arg-to-shell-ts
    const text = execSync(`journalctl -p ${level} -n 20`).toString();
    return { messages: [{ role: "user", content: { type: "text", text } }] };
  },
);

low.setRequestHandler(ListResourcesRequestSchema, async (request) => {
  // ok: mcp-tool-arg-to-shell-ts
  const text = execSync("ls /srv/runbooks " + (request.params?.cursor ?? "")).toString();
  return { resources: text.split("\n").map((name) => ({ uri: `runbook://${name}`, name })) };
});

async function readConfig(uri: URL) {
  // ok: mcp-tool-arg-to-shell-ts
  const text = execSync("cat /etc/app/" + uri.pathname).toString();
  return { contents: [{ uri: uri.href, text }] };
}

server.registerResource("config", "config://app/settings.toml", {}, readConfig);

function notRegistered({ unit }: { unit: string }) {
  // ok: mcp-tool-arg-to-shell-ts
  return execSync("systemctl status " + unit).toString();
}
