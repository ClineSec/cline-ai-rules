// Drafts the "upstream changes" section of a failed run's report: when a dependency bump broke
// the build, read the dependency's release notes and say which change is the likely cause.
import { query, type Options } from "@anthropic-ai/claude-agent-sdk";

export interface UpstreamNotesInput {
  pkg: string;
  from: string;
  to: string;
  logExcerpt: string;
}

// Release notes live on GitHub, the registry, or the project's own site, so the agent may read
// any page; the repo itself stays read-only.
const UPSTREAM_TOOLS = ["Read", "Grep", "WebFetch"];

export function upstreamOptions(cwd: string): Options {
  return {
    cwd,
    allowedTools: UPSTREAM_TOOLS,
    disallowedTools: ["Bash", "Write", "Edit"],
    permissionMode: "default",
    maxTurns: 12,
  };
}

// The changelog check only needs the registry.
export function registryOptions(cwd: string): Options {
  return {
    cwd,
    allowedTools: ["Read", "WebFetch(domain:registry.npmjs.org)", "WebFetch(domain:*.npmjs.com)"],
    maxTurns: 4,
  };
}

export async function upstreamNotes(input: UpstreamNotesInput, cwd: string): Promise<string> {
  const prompt = [
    `The build broke after ${input.pkg} went from ${input.from} to ${input.to}.`,
    "Read its release notes for that range and name the change most likely to explain this log:",
    input.logExcerpt,
  ].join("\n\n");
  let text = "";
  for await (const message of query({ prompt, options: upstreamOptions(cwd) })) {
    if (message.type === "result" && message.subtype === "success") text = message.result;
  }
  return text;
}
