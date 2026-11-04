import { query, type Options } from "@anthropic-ai/claude-agent-sdk";

const ALLOWED_TOOLS = [
  "Read",
  // ruleid: agent-allowlist-webfetch-any-domain-ts
  "WebFetch",
  // ok: agent-allowlist-webfetch-any-domain-ts
  "WebFetch(domain:docs.example.com)",
];

const DISALLOWED_TOOLS = [
  // ok: agent-allowlist-webfetch-any-domain-ts
  "WebFetch",
];

export function researchOptions(cwd: string): Options {
  return {
    cwd,
    allowedTools: [
      "Grep",
      // ruleid: agent-allowlist-webfetch-any-domain-ts
      "WebFetch(domain:*)",
      // ok: agent-allowlist-webfetch-any-domain-ts
      "WebSearch",
    ],
    disallowedTools: DISALLOWED_TOOLS,
    permissionMode: "default",
  };
}

export async function changelog(prompt: string) {
  for await (const message of query({
    prompt,
    options: {
      // ruleid: agent-allowlist-webfetch-any-domain-ts
      allowedTools: ["Read", "WebFetch(domain:*.dev)"],
      agents: {
        reader: {
          description: "Reads linked pages",
          prompt: "Read the pages you are given.",
          // ok: agent-allowlist-webfetch-any-domain-ts
          tools: ["WebFetch"],
        },
      },
    },
  })) {
    console.log(message);
  }
}

export const yolo: Options = {
  // ok: agent-allowlist-webfetch-any-domain-ts
  allowedTools: ["WebFetch"],
  permissionMode: "bypassPermissions",
};

export const docsOnly: Options = {
  // ok: agent-allowlist-webfetch-any-domain-ts
  allowedTools: ["Read", "WebFetch(domain:*.example.com)"],
  // ok: agent-allowlist-webfetch-any-domain-ts
  disallowedTools: ["WebFetch(domain:*)"],
};

export const defaults = { allowedTools: ALLOWED_TOOLS };

const READ_ONLY_TOOLS = ["Read", "Grep", "Glob"];
export const RESEARCH_TOOLS = [
  ...READ_ONLY_TOOLS,
  // ruleid: agent-allowlist-webfetch-any-domain-ts
  "WebFetch",
] as const;
export const riskyTools: string[] = [
  // ok: agent-allowlist-webfetch-any-domain-ts
  "WebFetch",
];

// A deny rule wins over the allow.
export const denied: Options = {
  // ok: agent-allowlist-webfetch-any-domain-ts
  allowedTools: ["Read", "WebFetch"],
  disallowedTools: ["WebFetch"],
};
