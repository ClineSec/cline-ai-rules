import { tool } from "ai";
import { tool as agentTool } from "@openai/agents";
import { tool as lcTool } from "@langchain/core/tools";
import { execFileSync, spawn } from "node:child_process";
import { execa } from "execa";
import { simpleGit } from "simple-git";
import { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";

const git = simpleGit("/srv/checkout");

export const gitDiff = tool({
  description: "Diff the working tree against a target.",
  inputSchema: z.object({ target: z.string() }),
  execute: async ({ target }) => {
    // ruleid: agent-tool-arg-option-injection-ts
    return execFileSync("git", ["diff", "--unified=3", target], { cwd: "/srv/checkout" }).toString();
  },
});

export const gitDiffSafe = tool({
  description: "Diff against a target, with -- before it.",
  inputSchema: z.object({ target: z.string() }),
  execute: async ({ target }) => {
    // ok: agent-tool-arg-option-injection-ts
    return execFileSync("git", ["diff", "--unified=3", "--", target]).toString();
  },
});

export const gitDiffPattern = tool({
  description: "Diff against a target that matches a ref pattern.",
  inputSchema: z.object({ target: z.string().regex(/^[\w./]+$/) }),
  execute: async ({ target }) => {
    // ok: agent-tool-arg-option-injection-ts
    return execFileSync("git", ["diff", "--unified=3", target]).toString();
  },
});

export const checkout = agentTool({
  name: "checkout",
  description: "Check out a branch.",
  parameters: z.object({ branch: z.string() }),
  async execute({ branch }) {
    // ruleid: agent-tool-arg-option-injection-ts
    await git.checkout(branch);
    return `Switched to ${branch}`;
  },
});

export const checkoutChecked = agentTool({
  name: "checkout_checked",
  description: "Check out a branch that can't be an option.",
  parameters: z.object({ branch: z.string() }),
  async execute({ branch }) {
    if (branch.startsWith("-")) throw new Error("branch names can't start with '-'");
    // ok: agent-tool-arg-option-injection-ts
    await git.checkout(branch);
    return `Switched to ${branch}`;
  },
});

export const search = lcTool(
  async ({ pattern }) => {
    // ruleid: agent-tool-arg-option-injection-ts
    const { stdout } = await execa("rg", ["--json", pattern, "/srv/checkout"]);
    return stdout;
  },
  { name: "search", description: "Search the checkout.", schema: z.object({ pattern: z.string() }) },
);

export const download = tool({
  description: "Download a file.",
  inputSchema: z.object({ url: z.string() }),
  execute: async (input) => {
    // ruleid: agent-tool-arg-option-injection-ts
    spawn("curl", ["--fail", "--location", input.url]);
    return "ok";
  },
});

// Not an agent tool: MCP tools belong to mcp-tool-arg-option-injection-ts.
const server = new McpServer({ name: "git-tools", version: "0.4.0" });
server.registerTool("git_checkout", { inputSchema: { branch: z.string() } }, async ({ branch }) => {
  // ok: agent-tool-arg-option-injection-ts
  await git.checkout(branch);
  return { content: [{ type: "text", text: branch }] };
});

// simple-git arrays and options objects are checked element by element, so a guard or a
// literal prefix inside them counts; log's `from` still starts an argument.
export const branchDiff = tool({
  description: "Diff a branch against main.",
  inputSchema: z.object({ branch: z.string() }),
  execute: async ({ branch }) => {
    // ok: agent-tool-arg-option-injection-ts
    return git.diff(["--stat", "--end-of-options", `main...${branch}`]);
  },
});

export const branchLog = tool({
  description: "Commits on a branch since main.",
  inputSchema: z.object({ branch: z.string() }),
  execute: async ({ branch }) => {
    // ok: agent-tool-arg-option-injection-ts
    return (await git.log({ from: "main", to: branch })).all.map((c) => c.message);
  },
});

export const logSince = tool({
  description: "Commits since a revision.",
  inputSchema: z.object({ since: z.string() }),
  execute: async ({ since }) => {
    // ruleid: agent-tool-arg-option-injection-ts
    return (await git.log({ from: since, to: "HEAD" })).all.map((c) => c.message);
  },
});
