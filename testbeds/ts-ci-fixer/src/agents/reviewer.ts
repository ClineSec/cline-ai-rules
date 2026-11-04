import { query, type AgentDefinition } from "@anthropic-ai/claude-agent-sdk";
import { baseOptions } from "../agentOptions.js";
import { config } from "../config.js";
import { gateTool } from "../permissions.js";
import { READ_ONLY_TOOLS } from "../toolsets.js";

const testRunner: AgentDefinition = {
  description: "Runs the test suite and reports failures",
  prompt: "Run the tests and summarize what failed.",
  tools: ["Bash", "Read"],
  // Subagents never run in bypass, whatever this says; the reviewer session sets the mode.
  permissionMode: "bypassPermissions",
};

export async function reviewPullRequest(checkoutDir: string, diff: string): Promise<string> {
  const options = baseOptions(checkoutDir, {
    permissionMode: config.reviewerPermissionMode,
    allowedTools: READ_ONLY_TOOLS,
    canUseTool: gateTool,
    agents: { "test-runner": testRunner },
  });

  let review = "";
  for await (const message of query({ prompt: `Review this diff:\n\n${diff}`, options })) {
    if (message.type === "result" && message.subtype === "success") {
      review = message.result;
    }
  }
  return review;
}
