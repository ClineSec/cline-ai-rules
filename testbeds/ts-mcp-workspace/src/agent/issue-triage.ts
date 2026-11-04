// Issue triage on the OpenAI Agents SDK: a router hands each cached issue to a labeler.
import { Agent, run } from "@openai/agents";

import { searchIssueCache } from "./issue-cache.js";

const bugLabeler = new Agent({
  name: "Bug labeler",
  instructions: "Pick bug labels (crash, regression, flaky) for the issue. Reply with labels only.",
});
const featureLabeler = new Agent({
  name: "Feature labeler",
  instructions: "Pick feature labels (api, cli, docs) for the issue. Reply with labels only.",
});
const router = Agent.create({
  name: "Issue router",
  instructions: "Decide whether the issue is a bug or a feature request and hand it off.",
  handoffs: [bugLabeler, featureLabeler],
});

const RUN_LIMITS = {
  // Router and labelers kept bouncing long issues past the default 10 turns.
  triage: { maxTurns: null },
  quick: { maxTurns: 20 },
};

export async function labelIssue(issueNumber: number): Promise<string> {
  const issue = searchIssueCache(issueNumber);
  const result = await run(router, issue, RUN_LIMITS.triage);
  return String(result.finalOutput ?? "");
}

export async function quickLabel(issueNumber: number): Promise<string> {
  const result = await run(router, searchIssueCache(issueNumber), RUN_LIMITS.quick);
  return String(result.finalOutput ?? "");
}
