// Dependency research on Mastra: reads the workspace's package list and summarizes upgrade risk.
import { Agent } from "@mastra/core/agent";
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

const PACKAGES = ["express", "execa", "simple-git", "zod"];

const listPackages = createTool({
  id: "list-packages",
  description: "List the workspace's runtime dependencies",
  inputSchema: z.object({}),
  execute: async () => ({ packages: PACKAGES }),
});

// The full audit walks every dependency's changelog, so it got far more than Mastra's 5 steps.
const FULL_AUDIT_STEPS = 2_000;

export const upgradeResearcher = new Agent({
  id: "upgrade-researcher",
  name: "Upgrade researcher",
  instructions: "Summarize the upgrade risk for each dependency in one line.",
  model: "openai/gpt-5",
  tools: { listPackages },
  defaultOptions: { maxSteps: 12 },
});

export async function quickRisk(): Promise<string> {
  const result = await upgradeResearcher.generate("Which dependency is riskiest to upgrade?");
  return result.text;
}

export async function fullAudit(): Promise<string> {
  const stream = await upgradeResearcher.stream("Audit every dependency's upgrade risk.", { maxSteps: FULL_AUDIT_STEPS });
  return await stream.text;
}
