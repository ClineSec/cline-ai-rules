import { ASSIST_AGENT_ID, letta } from "./assistant-memory";
import { findRelevantArticles } from "./help-center";

const KNOWN_ISSUES_QUERIES = ["outage", "degraded performance", "login problems", "billing errors"];

// Nightly job: refresh the agent-assist panel's "known issues" core memory block from the
// help-center articles that match the usual incident searches, so drafts mention them.
export async function refreshKnownIssues() {
  const matches = (await Promise.all(KNOWN_ISSUES_QUERIES.map((q) => findRelevantArticles(q, 2)))).flat();
  const known = matches.map((a) => `## ${a.title}\n${a.content}`).join("\n\n");
  await letta.agents.blocks.update("known_issues", {
    agent_id: ASSIST_AGENT_ID,
    value: known,
    description: "Current known issues from the help center",
  });
}

// A staff member pins a note for the assistant from the admin panel; staff wrote it.
export async function pinStaffNote(note: string, author: string) {
  await letta.agents.passages.create(ASSIST_AGENT_ID, { text: note, tags: ["staff-note", author] });
}
