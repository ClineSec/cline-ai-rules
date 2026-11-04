import { randomUUID } from "node:crypto";
import { join } from "node:path";
import { Role, type AgentCard, type Message } from "@a2a-js/sdk";
import { AgentEvent, type AgentExecutor, type ExecutionEventBus, type RequestContext } from "@a2a-js/sdk/server";
import { config } from "../config.js";
import { proposeFix } from "../agents/fixer.js";

const PUBLIC_URL = process.env.CI_FIXER_A2A_URL ?? "https://ci-fixer.example.com";

/** What other agents (the on-call agent, the release bot) see when they look the fixer up. */
export const fixerCard: AgentCard = {
  name: "ci-fixer",
  description: "Proposes the smallest change that makes a failing CI run pass.",
  version: "0.3.1",
  supportedInterfaces: [{ url: `${PUBLIC_URL}/a2a/jsonrpc`, protocolBinding: "JSONRPC", protocolVersion: "1.0" }],
  capabilities: { streaming: false, pushNotifications: false },
  defaultInputModes: ["text/plain"],
  defaultOutputModes: ["text/plain"],
  skills: [
    {
      id: "fix-failing-run",
      name: "Fix a failing run",
      description: "Give a repo, a branch, and a log excerpt; returns a summary of the proposed fix.",
      tags: ["ci", "fix"],
      examples: ["example-org/web main: npm test fails in src/date.test.ts"],
    },
  ],
} as AgentCard;

function agentText(contextId: string, text: string): Message {
  return {
    role: Role.ROLE_AGENT,
    messageId: randomUUID(),
    contextId,
    parts: [{ content: { $case: "text", value: text }, mediaType: "text/plain" }],
  } as Message;
}

/** One fix attempt per request: "<owner/repo> <branch>: <log excerpt>". */
export class FixerExecutor implements AgentExecutor {
  async execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void> {
    const text = requestContext.userMessage.parts
      .map((part) => (part.content?.$case === "text" ? part.content.value : ""))
      .join("\n");
    const match = /^(\S+)\s+(\S+):\s*([\s\S]*)$/.exec(text.trim());
    if (!match) {
      eventBus.publish(AgentEvent.message(agentText(requestContext.contextId, "Send '<owner/repo> <branch>: <log excerpt>'.")));
      eventBus.finished();
      return;
    }
    const [, repo, branch, logExcerpt] = match;
    const checkoutDir = join(config.workRoot, repo.replaceAll("/", "__"), branch);
    const summary = await proposeFix({ repo, branch, checkoutDir, logExcerpt });
    eventBus.publish(AgentEvent.message(agentText(requestContext.contextId, summary)));
    eventBus.finished();
  }

  async cancelTask(): Promise<void> {}
}
