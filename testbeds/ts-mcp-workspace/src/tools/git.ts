import { execFile } from "node:child_process";
import { promisify } from "node:util";

import type { McpServer } from "@modelcontextprotocol/server";
import { simpleGit } from "simple-git";
import { z } from "zod";

import { clip, config } from "../config.js";

const execFileAsync = promisify(execFile);
const git = simpleGit(config.workspace);

const text = (value: string) => ({ content: [{ type: "text" as const, text: clip(value) }] });

export function registerGitTools(server: McpServer): void {
  server.registerTool(
    "git_status",
    { description: "Short status of the working tree", inputSchema: z.object({}) },
    async () => text((await git.status()).files.map((f) => `${f.working_dir} ${f.path}`).join("\n")),
  );

  server.registerTool(
    "git_diff",
    {
      description: "Diff the working tree against a branch, tag, or commit",
      inputSchema: z.object({ target: z.string(), contextLines: z.number().int().min(0).max(20).default(3) }),
    },
    async ({ target, contextLines }) => text(await git.diff([`--unified=${contextLines}`, target])),
  );

  server.registerTool(
    "git_log",
    {
      description: "One-line history for a ref",
      inputSchema: z.object({ ref: z.string().default("HEAD"), maxCount: z.number().int().max(200).default(20) }),
    },
    async ({ ref, maxCount }) => {
      const { stdout } = await execFileAsync(
        "git",
        ["log", "--oneline", `--max-count=${maxCount}`, "--end-of-options", ref],
        { cwd: config.workspace },
      );
      return text(stdout);
    },
  );

  server.registerTool(
    "git_checkout",
    { description: "Switch to an existing branch", inputSchema: z.object({ branch: z.string() }) },
    async ({ branch }) => {
      if (branch.startsWith("-")) {
        throw new Error(`Refusing a branch name that looks like an option: ${branch}`);
      }
      await git.checkout(branch);
      return text(`Switched to ${branch}`);
    },
  );

  server.registerTool(
    "git_branch_log",
    { description: "Commits on a remote branch that are not on main", inputSchema: z.object({ branch: z.string() }) },
    async ({ branch }) => {
      const { stdout } = await execFileAsync("git", ["log", "--oneline", `main..origin/${branch}`], {
        cwd: config.workspace,
      });
      return text(stdout);
    },
  );

  server.registerTool(
    "git_show",
    {
      description: "Show a commit",
      inputSchema: z.object({ rev: z.string(), statOnly: z.boolean().default(true) }),
    },
    async ({ rev, statOnly }) => text(await git.show(statOnly ? ["--stat", rev] : [rev])),
  );
}
