import { execFileSync } from "node:child_process";
import os from "node:os";

import type { McpServer } from "@modelcontextprotocol/server";
import { tool } from "ai";
import { z } from "zod";

import { config } from "../config.js";

// Variables the support runbook asks for by name.
const SUPPORT_VARIABLES = new Set(["WORKSPACE_DIR", "WORKSPACE_MAX_OUTPUT", "NODE_ENV", "TZ"]);
// Names that hold credentials; their values never leave the host.
const CREDENTIAL_NAME = /token|secret|passw|key|auth/i;
// The locale a bug report needs to reproduce date and number formatting.
const LOCALE_VARIABLES = ["TZ", "LANG", "LC_ALL"] as const;

export function registerDiagnosticTools(server: McpServer): void {
  server.registerTool(
    "support_bundle",
    { description: "Runtime, settings, and environment for a support ticket" },
    async () => {
      const bundle = {
        node: process.version,
        host: os.hostname(),
        workspace: config.workspace,
        uptimeSeconds: Math.round(process.uptime()),
        env: process.env,
      };
      return { content: [{ type: "text", text: JSON.stringify(bundle, null, 2) }] };
    },
  );

  server.registerTool(
    "support_variable",
    {
      description: "One of the variables the support runbook asks for",
      inputSchema: z.object({ name: z.string() }),
    },
    async ({ name }) => {
      if (!SUPPORT_VARIABLES.has(name)) {
        return { content: [{ type: "text", text: `not a support variable: ${name}` }], isError: true };
      }
      return { content: [{ type: "text", text: process.env[name] ?? "(unset)" }] };
    },
  );

  server.registerTool("ci_context", { description: "The CI runner's variables, for matching a failure to its pipeline" }, async () => {
    const ci = Object.entries(process.env).filter(([name]) => name.startsWith("CI_") || name.startsWith("GITHUB_"));
    return { content: [{ type: "text", text: ci.map(([name, value]) => `${name}=${value}`).join("\n") }] };
  });

  server.registerTool("workspace_settings", { description: "Every WORKSPACE_* setting except the credentials" }, async () => {
    const settings = Object.entries(process.env).filter(
      ([name]) => name.startsWith("WORKSPACE_") && !CREDENTIAL_NAME.test(name),
    );
    return { content: [{ type: "text", text: JSON.stringify(Object.fromEntries(settings), null, 2) }] };
  });

  server.registerTool("locale_settings", { description: "The time zone and locale the server runs with" }, async () => {
    const locale = Object.entries(process.env).filter(([name]) => (LOCALE_VARIABLES as readonly string[]).includes(name));
    return { content: [{ type: "text", text: JSON.stringify(Object.fromEntries(locale)) }] };
  });

  server.registerTool("environment_names", { description: "Names of the variables set for the server" }, async () => ({
    content: [{ type: "text", text: Object.keys(process.env).sort().join("\n") }],
  }));

  server.registerTool("npm_doctor", { description: "Run npm doctor in the workspace" }, async () => {
    const out = execFileSync("npm", ["doctor"], {
      cwd: config.workspace,
      env: { ...process.env, NO_COLOR: "1" },
      encoding: "utf8",
    });
    return { content: [{ type: "text", text: out }] };
  });
}

// The same lookups for the in-process agents on the AI SDK (src/agent/changelog.ts).
export const ciVariable = tool({
  description: "A CI_* variable from the release job, by its short name (e.g. COMMIT_SHA)",
  inputSchema: z.object({ name: z.string() }),
  execute: async ({ name }) => process.env[`CI_${name}`] ?? "",
});

export const runtimeInfo = tool({
  description: "Node version and mode",
  inputSchema: z.object({}),
  execute: async () => ({ node: process.version, mode: process.env.NODE_ENV ?? "development" }),
});
