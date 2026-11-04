import { tool, dynamicTool } from "ai";
import { tool as agentTool } from "@openai/agents";
import { tool as lcTool, DynamicStructuredTool, StructuredTool } from "@langchain/core/tools";
import { exec, execFile, execSync, spawn } from "node:child_process";
import { promisify } from "node:util";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const execAsync = promisify(exec);
const ALLOWED_UNITS = new Set(["nginx", "postgres"]);

// --- Vercel AI SDK ---------------------------------------------------------------------------

export const runShell = tool({
  description: "Run a shell command.",
  inputSchema: z.object({ command: z.string() }),
  execute: async ({ command }) => {
    // ruleid: agent-tool-arg-to-shell-ts
    const { stdout } = await execAsync(command);
    return stdout;
  },
});

export const gitLog = tool({
  description: "Show the log for a ref.",
  inputSchema: z.object({ ref: z.string(), count: z.number().int() }),
  execute: async ({ ref, count }) => {
    // ok: agent-tool-arg-to-shell-ts
    execSync(`git log -n ${count} --oneline`);
    // ok: agent-tool-arg-to-shell-ts
    return new Promise((resolve) => execFile("git", ["log", "--oneline", "--", ref], (_e, out) => resolve(out)));
  },
});

export const restart = tool({
  description: "Restart a service.",
  inputSchema: z.object({
    unit: z.enum(["nginx", "postgres"]),
    name: z.string().regex(/^[a-z0-9-]+$/),
  }),
  execute: async (input) => {
    // ok: agent-tool-arg-to-shell-ts
    execSync(`systemctl restart ${input.unit}`);
    // ok: agent-tool-arg-to-shell-ts
    return execSync(`logger restarted-${input.name}`).toString();
  },
});

export const restartChecked = tool({
  description: "Restart an allowlisted service.",
  inputSchema: z.object({ unit: z.string() }),
  execute: async ({ unit }) => {
    if (!ALLOWED_UNITS.has(unit)) throw new Error("unknown unit");
    // ok: agent-tool-arg-to-shell-ts
    return execSync(`systemctl restart ${unit}`).toString();
  },
});

export const calc = dynamicTool({
  description: "Evaluate an arithmetic expression.",
  inputSchema: z.object({ expression: z.string() }),
  execute: async (input: any) => {
    // ruleid: agent-tool-arg-to-shell-ts
    return String(eval(input.expression));
  },
});

async function diskUsage({ path }: { path: string }) {
  // ruleid: agent-tool-arg-to-shell-ts
  return execSync(`du -sh ${path}`).toString();
}

export const du = tool({ description: "du", inputSchema: z.object({ path: z.string() }), execute: diskUsage });

const tailLog = async ({ name, lines }: { name: string; lines: number }) => {
  // ruleid: agent-tool-arg-to-shell-ts
  return execSync(`tail -n ${lines} /var/log/${name}`).toString();
};

export const tail = tool({
  description: "Tail a log file.",
  inputSchema: z.object({ name: z.string(), lines: z.number() }),
  execute: tailLog,
});

function onTick(job: { command: string }) {
  // A timer callback, not a tool: the name is passed to setInterval, not to tool().
  // ok: agent-tool-arg-to-shell-ts
  return execSync(job.command).toString();
}

setInterval(onTick, 60_000, { command: "uptime" });

function notATool(command: string) {
  // ok: agent-tool-arg-to-shell-ts
  return execSync(command).toString();
}

// --- OpenAI Agents JS ------------------------------------------------------------------------

export const archive = agentTool({
  name: "archive",
  description: "Archive a folder.",
  parameters: z.object({ folder: z.string() }),
  async execute(input) {
    // ruleid: agent-tool-arg-to-shell-ts
    spawn("tar", ["czf", "/tmp/archive.tgz", input.folder], { shell: true });
    return "done";
  },
});

// --- LangChain.js ----------------------------------------------------------------------------

export const ping = lcTool(
  async ({ host }) => {
    // ruleid: agent-tool-arg-to-shell-ts
    return execSync("ping -c 1 " + host).toString();
  },
  { name: "ping", description: "Ping a host.", schema: z.object({ host: z.string() }) },
);

export const runScript = new DynamicStructuredTool({
  name: "run_script",
  description: "Run a script with bash.",
  schema: z.object({ script: z.string() }),
  // ruleid: agent-tool-arg-to-shell-ts
  func: async ({ script }) => String(spawn("bash", ["-c", script])),
});

class GrepTool extends StructuredTool {
  name = "grep";
  description = "Search the logs.";
  schema = z.object({ pattern: z.string() });

  async _call({ pattern }: { pattern: string }) {
    // ruleid: agent-tool-arg-to-shell-ts
    return execSync(`grep -n ${pattern} /var/log/app.log`).toString();
  }

  describe(pattern: string) {
    // ok: agent-tool-arg-to-shell-ts
    return execSync(pattern).toString();
  }
}

// --- Not an agent tool: MCP tools belong to mcp-tool-arg-to-shell-ts ---------------------------

const server = new McpServer({ name: "ops", version: "1.0.0" });
server.registerTool("shell", { inputSchema: { command: z.string() } }, async ({ command }) => {
  // ok: agent-tool-arg-to-shell-ts
  return { content: [{ type: "text", text: execSync(command).toString() }] };
});
