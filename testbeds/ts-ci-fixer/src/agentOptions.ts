import type { Options } from "@anthropic-ai/claude-agent-sdk";
import { config } from "./config.js";

/** Options every agent shares; callers add their own mode and tools on top. */
export function baseOptions(cwd: string, extra: Partial<Options> = {}): Options {
  return {
    cwd,
    model: config.model,
    maxTurns: config.maxTurns,
    maxBudgetUsd: config.maxBudgetUsd,
    settingSources: [],
    ...extra,
  };
}
