import { Agent, run, tool, type RunContext } from "@openai/agents";
import { z } from "zod";

// Drafts a postmortem for a deploy incident (OpenAI Agents SDK). The draft starts from the
// incident's status-page updates; the deploy log is a tool so the agent can check the timeline.

const STATUS_API_URL = process.env.STATUS_API_URL ?? "https://status.example.com/api/v2";
const DEPLOY_LOG_URL = process.env.DEPLOY_LOG_URL ?? "https://deploys.example.com/api/log";

const DRAFT_RULES =
  "Draft a blameless postmortem with these sections: summary, impact, timeline, root cause, " +
  "follow-ups. Never name individuals.";

const DIGEST_RULES =
  "Write one plain-language sentence for the customer status digest: what is affected and " +
  "what happens next. No internal service names.";

interface PostmortemContext {
  incidentId: string;
}

interface StatusUpdate {
  status: "investigating" | "identified" | "monitoring" | "resolved";
  body: string;
}

async function postmortemInstructions(runContext: RunContext<PostmortemContext>): Promise<string> {
  const resp = await fetch(`${STATUS_API_URL}/incidents/${runContext.context.incidentId}/updates`);
  if (!resp.ok) {
    return DRAFT_RULES;
  }
  const updates: StatusUpdate[] = await resp.json();
  for (const update of updates) {
    if (update.status === "resolved") {
      return `${DRAFT_RULES}\n\nThe resolution note from the status page:\n${update.body}`;
    }
  }
  return `${DRAFT_RULES}\n\nThe incident is not resolved yet (${updates.length} updates so far).`;
}

export const postmortemAgent = new Agent<PostmortemContext>({
  name: "postmortem",
  instructions: postmortemInstructions,
  tools: [
    tool({
      name: "deploy_log",
      description: "Read the deploy log for a service over the incident window.",
      parameters: z.object({ service: z.string(), since: z.string(), until: z.string() }),
      execute: async ({ service, since, until }) => {
        const query = new URLSearchParams({ service, since, until });
        const resp = await fetch(`${DEPLOY_LOG_URL}?${query}`);
        const logText = await resp.text();
        return logText.slice(-20_000);
      },
    }),
  ],
});

export async function draftPostmortem(incidentId: string): Promise<string> {
  const result = await run(postmortemAgent, "Draft the postmortem.", { context: { incidentId } });
  return String(result.finalOutput ?? "");
}

// Customer status digest: one short-lived agent per open incident, each starting from that
// incident's latest status-page update.
export async function draftStatusDigest(incidentIds: string[]): Promise<string[]> {
  return Promise.all(
    incidentIds.map(async (incidentId) => {
      const digestAgent = new Agent({
        name: "status-digest",
        instructions: async () => {
          const resp = await fetch(`${STATUS_API_URL}/incidents/${incidentId}/updates`);
          const updates: StatusUpdate[] = resp.ok ? await resp.json() : [];
          if (updates.length > 0) {
            return `${DIGEST_RULES}\n\nLatest status-page update:\n${updates[updates.length - 1].body}`;
          }
          return DIGEST_RULES;
        },
      });
      const result = await run(digestAgent, "Write the digest entry.");
      return String(result.finalOutput ?? "");
    }),
  );
}
