#!/usr/bin/env node
// A second, smaller server for the pull request review panel: drafts review comments and
// titles with the client's own model. Run as `workspace-review` next to `workspace-mcp`.
import { McpServer } from "@modelcontextprotocol/server";
import { StdioServerTransport } from "@modelcontextprotocol/server/stdio";
import { simpleGit } from "simple-git";
import { z } from "zod";

import { clip, config } from "./config.js";
import { askHost } from "./sampling.js";

const git = simpleGit(config.workspace);

const REVIEW_PROMPT =
  "You review pull requests. List correctness problems first, then risky changes, then style. " +
  "Quote the hunk you mean. Say 'nothing to flag' when there is nothing.";

const text = (value: string) => ({ content: [{ type: "text" as const, text: clip(value) }] });

export function createReviewServer(): McpServer {
  const server = new McpServer({ name: "workspace-review", version: "1.2.0" });

  server.registerTool(
    "review_branch",
    {
      description: "Draft review comments for the diff between a branch and main",
      inputSchema: z.object({ branch: z.string() }),
    },
    async ({ branch }) => {
      const diff = await git.diff(["--end-of-options", `main...${branch}`]);
      return text(await askHost(server, `Review this diff:\n\n${diff}`, { systemPrompt: REVIEW_PROMPT, maxTokens: 1200 }));
    },
  );

  server.registerTool(
    "suggest_title",
    { description: "Suggest a pull request title for a branch", inputSchema: z.object({ branch: z.string() }) },
    async ({ branch }) => {
      const log = await git.log({ from: "main", to: branch });
      const subjects = log.all.map((c) => c.message).join("\n");
      // A title only needs the commit subjects.
      return text(await askHost(server, `One short PR title for:\n${subjects}`, { includeContext: "none", maxTokens: 30 }));
    },
  );

  server.registerTool(
    "explain_hunk",
    {
      description: "Explain one diff hunk in plain words",
      inputSchema: z.object({ hunk: z.string(), thorough: z.boolean().default(false) }),
    },
    async ({ hunk, thorough }, ctx) => {
      const result = await ctx.mcpReq.requestSampling({
        messages: [{ role: "user", content: { type: "text", text: `Explain this change:\n${hunk}` } }],
        maxTokens: thorough ? 800 : 250,
        includeContext: thorough ? "allServers" : "thisServer",
      });
      return text(result.content.type === "text" ? result.content.text : "");
    },
  );

  server.registerTool(
    "changelog_line",
    { description: "One changelog line for a commit", inputSchema: z.object({ sha: z.string() }) },
    async ({ sha }, ctx) => {
      const show = await git.show(["--stat", "--end-of-options", sha]);
      const result = await ctx.mcpReq.requestSampling({
        messages: [{ role: "user", content: { type: "text", text: `One changelog line for:\n${show}` } }],
        maxTokens: 60,
        // Earlier results from this server are enough here.
        includeContext: "thisServer",
      });
      return text(result.content.type === "text" ? result.content.text : "");
    },
  );

  return server;
}

const transport = new StdioServerTransport();
await createReviewServer().connect(transport);
