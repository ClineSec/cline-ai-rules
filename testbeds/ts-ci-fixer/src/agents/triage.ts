import { query } from "@anthropic-ai/claude-agent-sdk";
import { baseOptions } from "../agentOptions.js";
import { integrations } from "../integrations.js";
import { DEPLOY_TRIAGE_TOOLS } from "../toolsets.js";

const { apiBase, org, authToken } = integrations.sentry;

interface SentryIssue {
  shortId: string;
  title: string;
  count: string;
}

/** Recent unresolved Sentry issues for a project, fetched with the service's own token. */
async function recentIssues(project: string): Promise<SentryIssue[]> {
  const res = await fetch(`${apiBase}/projects/${org}/${project}/issues/?query=is:unresolved`, {
    headers: { Authorization: `Bearer ${authToken}` },
  });
  return (await res.json()) as SentryIssue[];
}

function triageInstructions(project: string): string {
  return [
    `You triage new Sentry errors for ${project} after a failed deploy.`,
    `Look up stack traces with curl ${apiBase}/organizations/${org}/issues/<id>/events/latest/`,
    `and send the header "Authorization: Bearer ${authToken}".`,
  ].join("\n");
}

export async function triageDeploy(checkoutDir: string, project: string): Promise<string> {
  const issues = await recentIssues(project);
  const known = issues.map((i) => `${i.shortId} ${i.title} (${i.count} events)`).join("\n");
  const options = baseOptions(checkoutDir, {
    permissionMode: "default",
    allowedTools: [...DEPLOY_TRIAGE_TOOLS],
    systemPrompt: triageInstructions(project),
  });

  let report = "";
  for await (const message of query({
    prompt: `The deploy of ${project} failed. Already known:\n${known}\nFind the new error and the commit that caused it.`,
    options,
  })) {
    if (message.type === "result" && message.subtype === "success") {
      report = message.result;
    }
  }
  return report;
}

/** Status-page note for the incident channel: the issue list is data, not the token. */
export async function incidentNote(checkoutDir: string, project: string): Promise<void> {
  const issues = await recentIssues(project);
  const options = baseOptions(checkoutDir, {
    permissionMode: "default",
    allowedTools: ["Read"],
    systemPrompt: `Write a two-line status note for ${integrations.statusUrl}. Open issues: ${issues.length}, top: ${issues[0]?.title ?? "none"}.`,
  });
  for await (const message of query({ prompt: `Summarize the ${project} incident.`, options })) {
    if (message.type === "result") {
      console.info(`incident note: ${message.subtype}`);
    }
  }
}
