import { query, type Options } from "@anthropic-ai/claude-agent-sdk";
import { baseOptions } from "../agentOptions.js";

/** Repairs Playwright specs that broke after a UI change. Runs from the nightly e2e job. */
const canUseTool: Options["canUseTool"] = async (_toolName, input) => ({ behavior: "allow", updatedInput: input });

export async function repairE2eSpecs(checkoutDir: string, failingSpecs: string[]): Promise<void> {
  const sdkOptions = baseOptions(checkoutDir, { canUseTool, allowedTools: ["Read", "Edit", "Bash(npx playwright test *)"] });
  for await (const message of query({
    prompt: `These Playwright specs fail on main:\n${failingSpecs.join("\n")}\nUpdate the selectors so they pass.`,
    options: sdkOptions,
  })) {
    if (message.type === "result") console.info(`e2e repair: ${message.subtype}`);
  }
}
