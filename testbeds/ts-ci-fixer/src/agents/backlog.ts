import { tool } from "@langchain/core/tools";
import { createAgent, humanInTheLoopMiddleware } from "langchain";
import { z } from "zod";

// Flaky-test backlog groomer (LangChain.js). Tool calls listed in interruptOn pause for a
// maintainer in the bot's review queue before they run.

const listIssues = tool(async ({ label }) => JSON.stringify({ label, issues: [] }), {
  name: "list_issues",
  description: "List open issues with a label.",
  schema: z.object({ label: z.string() }),
});

const closeIssue = tool(async ({ number }) => `closed #${number}`, {
  name: "close_issue",
  description: "Close an issue as fixed or stale.",
  schema: z.object({ number: z.number() }),
});

const addLabel = tool(async ({ number, label }) => `labeled #${number} ${label}`, {
  name: "add_label",
  description: "Add a label to an issue.",
  schema: z.object({ number: z.number(), label: z.string() }),
});

// Stale flaky-test issues are closed by the hundred; reviewing each close was too slow.
const BACKLOG_REVIEW = {
  list_issues: false,
  close_issue: false,
  add_label: { allowedDecisions: ["approve", "reject"] as ("approve" | "reject")[] },
};

export const backlogAgent = createAgent({
  model: "openai:gpt-5",
  tools: [listIssues, closeIssue, addLabel],
  middleware: [humanInTheLoopMiddleware({ interruptOn: BACKLOG_REVIEW })],
});
