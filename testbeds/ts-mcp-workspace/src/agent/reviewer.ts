// A review agent that checks a branch, with its own in-process tools.
import { spawnSync } from "node:child_process";

import { createSdkMcpServer, query, tool } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

import { config } from "../config.js";

const CHECKS = {
  lint: ["npx", "eslint", "src"],
  types: ["npx", "tsc", "--noEmit"],
} as const;

const reviewTools = createSdkMcpServer({
  name: "review",
  version: "1.0.0",
  tools: [
    tool("run_check", "Run one of the standard checks", { check: z.enum(["lint", "types"]) }, async ({ check }) => {
      const [bin, ...args] = CHECKS[check];
      const result = spawnSync(bin, args, { cwd: config.workspace, encoding: "utf8" });
      return { content: [{ type: "text", text: result.stdout }] };
    }),
    tool("run_command", "Run a shell command in the workspace", { command: z.string() }, async ({ command }) => {
      const result = spawnSync("bash", ["-lc", command], { cwd: config.workspace, encoding: "utf8" });
      return { content: [{ type: "text", text: result.stdout + result.stderr }] };
    }),
  ],
});

export async function reviewBranch(branch: string): Promise<string> {
  let summary = "";
  for await (const message of query({
    prompt: `Review the changes on ${branch} and summarize any problems.`,
    options: {
      cwd: config.workspace,
      mcpServers: { review: reviewTools },
      allowedTools: ["Read", "Grep", "mcp__review__run_check", "mcp__review__run_command"],
    },
  })) {
    if (message.type === "result" && message.subtype === "success") summary = message.result;
  }
  return summary;
}
