// Changelog and release-notes drafting on the AI SDK's ToolLoopAgent.
import { openai } from "@ai-sdk/openai";
import { hasToolCall, isStepCount, tool, ToolLoopAgent } from "ai";
import { simpleGit } from "simple-git";
import { z } from "zod";

import { config } from "../config.js";

const recentCommits = tool({
  description: "List the subjects of the last 50 commits on the current branch",
  inputSchema: z.object({}),
  execute: async () => {
    const log = await simpleGit(config.workspace).log({ maxCount: 50 });
    return log.all.map((c) => c.message).join("\n");
  },
});

const submitChangelog = tool({
  description: "Submit the finished changelog entry",
  inputSchema: z.object({ entry: z.string() }),
  execute: async ({ entry }) => ({ saved: entry.length }),
});

// Finishes when the model submits; long branches needed more than the default 20 steps.
export const changelogAgent = new ToolLoopAgent({
  model: openai("gpt-5"),
  instructions: "Draft a changelog entry for the current branch from its commit subjects, then submit it.",
  tools: { recentCommits, submitChangelog },
  stopWhen: [hasToolCall("submitChangelog")],
});

export const releaseNotesAgent = new ToolLoopAgent({
  model: openai("gpt-5"),
  instructions: "Draft short release notes from the commit subjects, then submit them.",
  tools: { recentCommits, submitChangelog },
  stopWhen: [isStepCount(30), hasToolCall("submitChangelog")],
});

export async function draftChangelog(): Promise<string> {
  const result = await changelogAgent.generate({ prompt: "Draft the changelog entry." });
  return result.text;
}
