import type { AgentDefinition } from "@anthropic-ai/claude-agent-sdk";
import { READ_ONLY_TOOLS } from "../toolsets.js";

// Sweep subagents edit on their own so the sweep session itself can stay in dontAsk.
const EDITOR_MODE: AgentDefinition["permissionMode"] = "acceptEdits";

function scoped(area: string): Pick<AgentDefinition, "description" | "prompt"> {
  return {
    description: `Fixes ${area} findings in the files it is given`,
    prompt: `Fix the ${area} findings in the listed files. Keep each change to the reported lines and list the files you changed.`,
  };
}

/** Subagents the nightly sweep can hand a batch of findings to. */
export const SWEEP_AGENTS = {
  "lint-fixer": { ...scoped("eslint"), tools: ["Read", "Edit", "Bash"], permissionMode: EDITOR_MODE },
  "type-fixer": { ...scoped("tsc"), tools: ["Read", "Edit"], permissionMode: EDITOR_MODE },
  "sweep-planner": { ...scoped("triage"), tools: READ_ONLY_TOOLS, permissionMode: "plan" },
} satisfies Record<string, AgentDefinition>;

/** Names the sweep prompt may hand work to; keeps the prompt and the registry in step. */
export type SweepAgentName = keyof typeof SWEEP_AGENTS;
export const SWEEP_AGENT_NAMES = Object.keys(SWEEP_AGENTS) as SweepAgentName[];
