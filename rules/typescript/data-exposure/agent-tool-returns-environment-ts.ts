import { execSync } from "node:child_process";
import { tool as agentTool } from "@openai/agents";
import { DynamicStructuredTool, tool as lcTool } from "@langchain/core/tools";
import { tool } from "ai";
import { z } from "zod";

export const environment = tool({
  description: "Environment variables of the build host",
  inputSchema: z.object({}),
  // ruleid: agent-tool-returns-environment-ts
  execute: async () => JSON.stringify(process.env),
});

export const readVariable = tool({
  description: "Read one environment variable",
  inputSchema: z.object({ name: z.string() }),
  execute: async ({ name }) => {
    // ruleid: agent-tool-returns-environment-ts
    return { name, value: process.env[name] };
  },
});

export const printenv = agentTool({
  name: "printenv",
  description: "Print the environment",
  parameters: z.object({}),
  async execute() {
    // ruleid: agent-tool-returns-environment-ts
    return execSync("env", { encoding: "utf8" });
  },
});

export const deployToken = lcTool(
  async () => {
    // ruleid: agent-tool-returns-environment-ts
    return `deploy token: ${process.env.DEPLOY_TOKEN}`;
  },
  { name: "deploy_token", description: "Token for the deploy API", schema: z.object({}) },
);

export const envSummary = new DynamicStructuredTool({
  name: "env_summary",
  description: "Environment summary",
  schema: z.object({}),
  func: async () => {
    // ruleid: agent-tool-returns-environment-ts
    return Object.entries(process.env).map(([k, v]) => `${k}=${v}`).join("\n");
  },
});

export const ciContext = tool({
  description: "CI variables for the release notes",
  inputSchema: z.object({}),
  // ruleid: agent-tool-returns-environment-ts
  execute: async () => Object.fromEntries(Object.entries(process.env).filter(([k]) => k.startsWith("CI_"))),
});

// An allowlist widened with a type assertion (a callback that starts with a parenthesized
// expression made OpenGrep 1.30.2 drop every finding in this file before the filter
// sanitizers skipped such callbacks and matched this form on its own).
const RELEASE_KEYS = ["CI_COMMIT_TAG", "CI_PIPELINE_ID"] as const;

export const releaseContext = tool({
  description: "Release tag and pipeline for the release notes",
  inputSchema: z.object({}),
  // ok: agent-tool-returns-environment-ts
  execute: async () => Object.fromEntries(Object.entries(process.env).filter(([k]) => (RELEASE_KEYS as readonly string[]).includes(k))),
});

// Near misses.

export const ciBranch = tool({
  description: "The CI branch",
  inputSchema: z.object({}),
  // ok: agent-tool-returns-environment-ts
  execute: async () => Object.fromEntries(Object.entries(process.env).filter(([k]) => k === "CI_COMMIT_BRANCH")),
});

export const nodeVersion = tool({
  description: "Runtime details",
  inputSchema: z.object({}),
  // ok: agent-tool-returns-environment-ts
  execute: async () => ({ node: process.version, env: process.env.NODE_ENV ?? "development" }),
});

export const providers = tool({
  description: "Which model providers are configured",
  inputSchema: z.object({}),
  // ok: agent-tool-returns-environment-ts
  execute: async () => ({ openai: Boolean(process.env.OPENAI_API_KEY), anthropic: "ANTHROPIC_API_KEY" in process.env }),
});

export const buildLog = tool({
  description: "Run the build",
  inputSchema: z.object({}),
  execute: async () => {
    const out = execSync("npm run build", { env: { ...process.env, CI: "1" }, encoding: "utf8" });
    // ok: agent-tool-returns-environment-ts
    return out.slice(-4000);
  },
});

export function envForCli(): string {
  // ok: agent-tool-returns-environment-ts
  return JSON.stringify(process.env);
}

async function hostEnvironment() {
  // ruleid: agent-tool-returns-environment-ts
  return Object.entries(process.env).map(([k, v]) => `${k}=${v}`).join("\n");
}

export const hostEnv = tool({
  description: "Environment of the agent host",
  inputSchema: z.object({}),
  execute: hostEnvironment,
});

// A filter callback that starts with a parenthesized fallback compared to a value. OpenGrep
// 1.30.2 aborted the whole file on it until the parenthesis guard covered operators.
export function openTickets(tickets: { status?: string }[], wanted: string) {
  return tickets.filter((ticket) => (ticket.status || "open") === wanted);
}
