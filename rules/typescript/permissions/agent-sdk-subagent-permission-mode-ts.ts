import { query, type AgentDefinition, type Options } from "@anthropic-ai/claude-agent-sdk";

const FIXER_MODE = "acceptEdits";

export const fixer: AgentDefinition = {
  description: "Fixes lint errors",
  prompt: "Fix the lint errors in the files you are given.",
  tools: ["Read", "Edit", "Bash"],
  // ruleid: agent-sdk-subagent-permission-mode-ts
  permissionMode: FIXER_MODE,
};

const shared = { description: "Labels new issues", prompt: "Read the issue and pick labels." };

export const options: Options = {
  permissionMode: "dontAsk",
  allowedTools: ["Read", "Grep"],
  agents: {
    fixer,
    triager: {
      ...shared,
      // ruleid: agent-sdk-subagent-permission-mode-ts
      permissionMode: "auto",
    },
    planner: {
      description: "Plans a refactor",
      prompt: "Plan the refactor without editing.",
      // ok: agent-sdk-subagent-permission-mode-ts
      permissionMode: "plan",
    } satisfies AgentDefinition,
    // Current SDKs ignore bypassPermissions on a subagent.
    legacy: {
      description: "Old release helper",
      prompt: "Cut the release.",
      // ok: agent-sdk-subagent-permission-mode-ts
      permissionMode: "bypassPermissions",
    },
  },
};

const shareds = (area: string) => ({ description: `Fixes ${area}`, prompt: `Fix the ${area} findings.` });

export const SWEEPERS: Record<string, AgentDefinition> = {
  // ruleid: agent-sdk-subagent-permission-mode-ts
  lint: { ...shareds("lint"), permissionMode: FIXER_MODE },
  // ok: agent-sdk-subagent-permission-mode-ts
  triage: { ...shareds("triage"), permissionMode: "plan" },
};

export const BY_AREA: { [area: string]: AgentDefinition } = {
  // ruleid: agent-sdk-subagent-permission-mode-ts
  docs: { ...shareds("docs"), permissionMode: "auto" },
};

// `satisfies` keeps the agent names as literal types; the entries are still definitions.
export const NIGHTLY = {
  // ruleid: agent-sdk-subagent-permission-mode-ts
  lint: { ...shareds("lint"), permissionMode: FIXER_MODE },
  // ok: agent-sdk-subagent-permission-mode-ts
  triage: { ...shareds("triage"), permissionMode: "plan" },
} satisfies Record<string, AgentDefinition>;

export const WEEKLY = {
  // ruleid: agent-sdk-subagent-permission-mode-ts
  deps: { ...shareds("deps"), permissionMode: "auto" },
} as const satisfies { [area: string]: AgentDefinition };

// ok: agent-sdk-subagent-permission-mode-ts
export const PRESETS = { quick: { label: "Quick", permissionMode: "auto" } } satisfies Record<string, { label: string; permissionMode: string }>;

// An untyped map of other objects is not a registry of definitions.
export const UI_MODES: Record<string, { label: string; permissionMode: string }> = {
  // ok: agent-sdk-subagent-permission-mode-ts
  quick: { label: "Quick", permissionMode: "auto" },
};

export const nightly = {
  description: "Fixes lint errors overnight",
  prompt: "Fix the lint errors.",
  // ruleid: agent-sdk-subagent-permission-mode-ts
  permissionMode: "auto" as const,
};

// The session's own mode is not a subagent's.
// ok: agent-sdk-subagent-permission-mode-ts
export const editSession: Options = { permissionMode: "acceptEdits", allowedTools: ["Read", "Edit"] };

export function reviewer(mode: AgentDefinition["permissionMode"]): AgentDefinition {
  // A run-time value can't be read here.
  // ok: agent-sdk-subagent-permission-mode-ts
  return { description: "Reviews diffs", prompt: "Review the diff.", permissionMode: mode };
}

export function clamp(requested: AgentDefinition["permissionMode"]): AgentDefinition {
  return {
    description: "Reviews diffs",
    prompt: "Review the diff.",
    // ok: agent-sdk-subagent-permission-mode-ts
    permissionMode: requested === "auto" ? "default" : requested,
  };
}

export async function run(prompt: string) {
  // ok: agent-sdk-subagent-permission-mode-ts
  for await (const message of query({ prompt, options: { ...options, permissionMode: "default" } })) {
    if (message.type === "result") return message;
  }
}
