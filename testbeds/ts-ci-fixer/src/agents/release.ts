import { query } from "@anthropic-ai/claude-agent-sdk";
import { baseOptions } from "../agentOptions.js";
import { integrations } from "../integrations.js";

const RELEASE_RULES = [
  "Bump the version with npm version, update CHANGELOG.md, and tag the release.",
  "Publish only from a clean working tree on main.",
].join("\n");

/** Cuts a release after a merge to main. */
export async function publishRelease(checkoutDir: string, bump: "patch" | "minor"): Promise<string> {
  const { registry, publishToken } = integrations.npm;
  const options = baseOptions(checkoutDir, {
    permissionMode: "acceptEdits",
    allowedTools: ["Read", "Edit", "Bash(npm version:*)", "Bash(npm publish:*)", "Bash(git tag:*)"],
    systemPrompt: {
      type: "preset",
      preset: "claude_code",
      append: `${RELEASE_RULES}\nPublish to ${registry} and authenticate with the token ${publishToken}.`,
    },
  });

  let tag = "";
  for await (const message of query({ prompt: `Release a ${bump} version.`, options })) {
    if (message.type === "result" && message.subtype === "success") {
      tag = message.result;
    }
  }
  return tag;
}

/** Dry run for the release checklist: the token reaches npm through the environment only. */
export async function checkRelease(checkoutDir: string): Promise<void> {
  const options = baseOptions(checkoutDir, {
    permissionMode: "default",
    allowedTools: ["Read", "Bash(npm publish --dry-run:*)"],
    systemPrompt: {
      type: "preset",
      preset: "claude_code",
      append: `${RELEASE_RULES}\nRun npm publish --dry-run against ${integrations.npm.registry}; the token is already in NPM_TOKEN.`,
    },
    env: { ...process.env, NPM_TOKEN: integrations.npm.publishToken },
  });
  for await (const message of query({ prompt: "Check that the package is ready to publish.", options })) {
    if (message.type === "result") {
      console.info(`release check: ${message.subtype}`);
    }
  }
}
