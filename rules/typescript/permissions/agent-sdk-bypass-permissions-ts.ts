import {
  query,
  type AgentDefinition,
  type CanUseTool,
  type Options,
  type PermissionMode,
} from "@anthropic-ai/claude-agent-sdk";

const SAFE_TOOLS = new Set(["Read", "Grep", "Glob"]);
const base: Options = { maxTurns: 20, cwd: "/srv/checkout" };

export async function fixLint(issueBody: string) {
  for await (const message of query({
    prompt: issueBody,
    options: {
      // ruleid: agent-sdk-bypass-permissions-ts
      permissionMode: "bypassPermissions",
      allowDangerouslySkipPermissions: true,
      maxTurns: 20,
    },
  })) {
    console.log(message);
  }
}

// ruleid: agent-sdk-bypass-permissions-ts
const AGENT_MODE: PermissionMode = "bypassPermissions";

// Reported where AGENT_MODE is assigned, not again here.
// ok: agent-sdk-bypass-permissions-ts
export const fromConstant: Options = { ...base, permissionMode: AGENT_MODE, allowDangerouslySkipPermissions: true };

const danger = "bypassPermissions";
// ruleid: agent-sdk-bypass-permissions-ts
export const fromOtherConstant: Options = { ...base, permissionMode: danger, allowDangerouslySkipPermissions: true };

export const fromEnvDefault: Options = {
  // ruleid: agent-sdk-bypass-permissions-ts
  permissionMode: (process.env.AGENT_PERMISSION_MODE as PermissionMode) ?? "bypassPermissions",
  allowDangerouslySkipPermissions: true,
};

export function ciOptions(ci: boolean): Options {
  // ruleid: agent-sdk-bypass-permissions-ts
  return { permissionMode: ci ? "bypassPermissions" : "default", allowDangerouslySkipPermissions: ci };
}

// ruleid: agent-sdk-bypass-permissions-ts
export const untyped = { permissionMode: "bypassPermissions" as const, allowDangerouslySkipPermissions: true };

// ruleid: agent-sdk-bypass-permissions-ts
export function buildOptions(cwd: string, mode: PermissionMode = "bypassPermissions"): Options {
  return { cwd, permissionMode: mode, allowDangerouslySkipPermissions: mode === "bypassPermissions" };
}

// The mode comes from the environment, so only the arming flag is a literal.
export const envDriven: Options = {
  permissionMode: process.env.AGENT_PERMISSION_MODE as PermissionMode,
  // ruleid: agent-sdk-bypass-permissions-ts
  allowDangerouslySkipPermissions: true,
};

export async function escalate(prompt: AsyncIterable<any>) {
  const q = query({
    prompt,
    // ruleid: agent-sdk-bypass-permissions-ts
    options: { permissionMode: "plan", allowDangerouslySkipPermissions: true },
  });
  // ruleid: agent-sdk-bypass-permissions-ts
  await q.setPermissionMode("bypassPermissions");
  return q;
}

export function mutate(opts: Options) {
  // ruleid: agent-sdk-bypass-permissions-ts
  opts.permissionMode = "bypassPermissions";
}

export const skipFlag: Options = {
  // ruleid: agent-sdk-bypass-permissions-ts
  extraArgs: { "dangerously-skip-permissions": null },
};

export const cliModeFlag: Options = {
  // ruleid: agent-sdk-bypass-permissions-ts
  extraArgs: { "permission-mode": "bypassPermissions" },
};

export const jobConfig = {
  model: "claude-sonnet-5-5",
  // ruleid: agent-sdk-bypass-permissions-ts
  fixerPermissionMode: (process.env.FIXER_PERMISSION_MODE as PermissionMode | undefined) ?? "bypassPermissions",
};

// ruleid: agent-sdk-bypass-permissions-ts
export const runJob = async (prompt: string, mode: PermissionMode = "bypassPermissions") =>
  query({ prompt, options: { permissionMode: mode } });

export const inlineSettings: Options = {
  // ruleid: agent-sdk-bypass-permissions-ts
  settings: { permissions: { defaultMode: "bypassPermissions" } },
};

const approveEverything: CanUseTool = async (_toolName, input) => ({ behavior: "allow", updatedInput: input });

async function approveAndLog(toolName: string, input: Record<string, unknown>) {
  console.log("tool", toolName);
  return { behavior: "allow" as const, updatedInput: input };
}

// ruleid: agent-sdk-bypass-permissions-ts
export const alwaysAllow: Options = { canUseTool: approveEverything };
// ruleid: agent-sdk-bypass-permissions-ts
export const loggedAllow: Options = { canUseTool: approveAndLog };
export const inlineAllow: Options = {
  // ruleid: agent-sdk-bypass-permissions-ts
  canUseTool: async (_name, input) => ({ behavior: "allow", updatedInput: input }),
};

// --- near misses ---------------------------------------------------------------------

// ok: agent-sdk-bypass-permissions-ts
export const readOnly: Options = { permissionMode: "default", allowedTools: ["Read", "Grep"], maxTurns: 20 };
// ok: agent-sdk-bypass-permissions-ts
export const edits: Options = { permissionMode: "acceptEdits", allowedTools: ["Read", "Edit"] };
// ok: agent-sdk-bypass-permissions-ts
export const planning: Options = { permissionMode: "plan", allowDangerouslySkipPermissions: false };
// ok: agent-sdk-bypass-permissions-ts
export const headless: Options = { permissionMode: "dontAsk", allowedTools: ["Read", "Bash(npm test)"] };
// ok: agent-sdk-bypass-permissions-ts
export const fromEnv: Options = { permissionMode: (process.env.AGENT_PERMISSION_MODE as PermissionMode) ?? "default" };

export function clamp(requested: PermissionMode): Options {
  // ok: agent-sdk-bypass-permissions-ts
  return { permissionMode: requested === "bypassPermissions" ? "default" : requested };
}

// A const named for the danger is a guard, and its use below is a comparison.
// ok: agent-sdk-bypass-permissions-ts
const BLOCKED_MODE = "bypassPermissions";

export function refuseBypass(opts: Options) {
  // ok: agent-sdk-bypass-permissions-ts
  if (opts.permissionMode === BLOCKED_MODE) {
    // ok: agent-sdk-bypass-permissions-ts
    throw new Error("bypassPermissions is not allowed for issue-driven runs");
  }
}

// Claude Code never applies bypassPermissions from a subagent definition.
export const withReviewer: Options = {
  agents: {
    reviewer: {
      description: "Reviews diffs",
      prompt: "Review the diff.",
      // ok: agent-sdk-bypass-permissions-ts
      permissionMode: "bypassPermissions",
    } satisfies AgentDefinition,
  },
};

const typedReviewer: AgentDefinition = {
  description: "Reviews diffs",
  prompt: "Review the diff.",
  // ok: agent-sdk-bypass-permissions-ts
  permissionMode: "bypassPermissions",
};

const untypedReviewer = {
  description: "Reviews diffs",
  tools: ["Read"],
  prompt: "Review the diff.",
  // ok: agent-sdk-bypass-permissions-ts
  permissionMode: "bypassPermissions" as const,
};

export const withTypedReviewer: Options = { agents: { reviewer: typedReviewer, other: untypedReviewer } };

export async function gate(toolName: string, input: Record<string, unknown>) {
  if (!SAFE_TOOLS.has(toolName)) {
    return { behavior: "deny" as const, message: `${toolName} needs a human` };
  }
  return { behavior: "allow" as const, updatedInput: input };
}

// Reported where jobConfig.fixerPermissionMode is assigned.
// ok: agent-sdk-bypass-permissions-ts
export const fromConfig: Options = { permissionMode: jobConfig.fixerPermissionMode };

// ok: agent-sdk-bypass-permissions-ts
export const gated: Options = { canUseTool: gate };
export const gatedInline: Options = {
  // ok: agent-sdk-bypass-permissions-ts
  canUseTool: async (name, input) =>
    SAFE_TOOLS.has(name) ? { behavior: "allow", updatedInput: input } : { behavior: "deny", message: "no" },
};

// A schema or allowlist of modes lists bypass as an accepted value; it sets nothing.
export const runnerSettings = z.object({
  // ok: agent-sdk-bypass-permissions-ts
  permissionMode: z.enum(["default", "acceptEdits", "bypassPermissions", "plan"]).optional(),
});
// ok: agent-sdk-bypass-permissions-ts
export const modeChoices = { permissionMode: ["default", "plan", "bypassPermissions"] as const };
// ok: agent-sdk-bypass-permissions-ts
export type BypassOnly = { permissionMode: "bypassPermissions"; maxTurns?: number };
export interface RunnerOverrides {
  // ok: agent-sdk-bypass-permissions-ts
  permissionMode?: "default" | "bypassPermissions";
}
