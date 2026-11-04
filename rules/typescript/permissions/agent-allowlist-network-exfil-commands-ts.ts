import { query, type Options } from "@anthropic-ai/claude-agent-sdk";

const ALLOWED_TOOLS = [
  "Read",
  // ruleid: agent-allowlist-network-exfil-commands-ts
  "Bash(curl:*)",
  // ok: agent-allowlist-network-exfil-commands-ts
  "Bash(curl -sf https://status.example.com/healthz)",
];

const DISALLOWED_TOOLS = [
  // ok: agent-allowlist-network-exfil-commands-ts
  "Bash(wget *)",
];

export function statusOptions(cwd: string): Options {
  return {
    cwd,
    allowedTools: [
      "Grep",
      // ruleid: agent-allowlist-network-exfil-commands-ts
      "Bash(dig +short *)",
      // ok: agent-allowlist-network-exfil-commands-ts
      "Bash(git log:*)",
    ],
    disallowedTools: DISALLOWED_TOOLS,
    permissionMode: "default",
  };
}

export async function deployCheck(prompt: string) {
  for await (const message of query({
    prompt,
    options: {
      // ruleid: agent-allowlist-network-exfil-commands-ts
      allowedTools: ["Read", "Bash(ssh deploy@build.example.com *)", "PowerShell(Invoke-WebRequest *)"],
      agents: {
        dns: {
          description: "Looks up hosts",
          prompt: "Look up the hosts you are given.",
          tools: ["Bash"],
        },
      },
    },
  })) {
    console.log(message);
  }
}

export const yolo: Options = {
  // ok: agent-allowlist-network-exfil-commands-ts
  allowedTools: ["Bash(curl:*)"],
  permissionMode: "bypassPermissions",
};

export const readonly: Options = {
  // ok: agent-allowlist-network-exfil-commands-ts
  allowedTools: ["Read", "Grep", "Bash(hostname)", "WebFetch(domain:docs.example.com)"],
  // ok: agent-allowlist-network-exfil-commands-ts
  disallowedTools: ["Bash(curl:*)", "Bash(wget:*)"],
};

export const defaults = { allowedTools: ALLOWED_TOOLS };

// A shared tool list in its own module, named for the agent rather than "allowed".
const READ_ONLY_TOOLS = ["Read", "Grep", "Glob"];
export const DEPLOY_TRIAGE_TOOLS = [
  ...READ_ONLY_TOOLS,
  // ruleid: agent-allowlist-network-exfil-commands-ts
  "Bash(curl:*)",
] as const;
export const riskyTools: string[] = [
  // ok: agent-allowlist-network-exfil-commands-ts
  "Bash(curl:*)",
];
export const SHELL_EXAMPLES = [
  // ok: agent-allowlist-network-exfil-commands-ts
  "Bash(curl:*)",
];
