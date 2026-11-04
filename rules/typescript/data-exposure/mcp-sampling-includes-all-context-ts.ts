import { inputRequired, McpServer } from "@modelcontextprotocol/server";
import type { CreateMessageRequest } from "@modelcontextprotocol/server";
import * as z from "zod/v4";

const server = new McpServer({ name: "review", version: "1.0.0" });

const WIDE_CONTEXT = "allServers";
const OWN_CONTEXT = "thisServer";

const user = (text: string) => [{ role: "user" as const, content: { type: "text" as const, text } }];

server.registerTool(
  "explain_failure",
  { description: "Explain a failed build log.", inputSchema: z.object({ log: z.string() }) },
  async ({ log }) => {
    const result = await server.server.createMessage({
      messages: user(`Why did this build fail?\n\n${log}`),
      maxTokens: 400,
      // ruleid: mcp-sampling-includes-all-context-ts
      includeContext: "allServers",
    });
    return { content: [{ type: "text", text: String(result.content) }] };
  },
);

server.registerTool(
  "review_diff",
  { description: "Review a diff.", inputSchema: z.object({ diff: z.string() }) },
  async ({ diff }, ctx) => {
    // ruleid: mcp-sampling-includes-all-context-ts
    const result = await ctx.mcpReq.requestSampling({ messages: user(diff), maxTokens: 600, includeContext: WIDE_CONTEXT });
    return { content: [{ type: "text", text: String(result.content) }] };
  },
);

server.registerTool(
  "summarize",
  { description: "Summarize text.", inputSchema: z.object({ text: z.string() }) },
  async ({ text }) =>
    inputRequired({
      inputRequests: {
        summary: inputRequired.createMessage({
          messages: user(`Summarize:\n${text}`),
          maxTokens: 200,
          // ruleid: mcp-sampling-includes-all-context-ts
          includeContext: "allServers" as const,
        }),
      },
    }),
);

const SAMPLING_DEFAULTS = {
  maxTokens: 500,
  // ruleid: mcp-sampling-includes-all-context-ts
  includeContext: "allServers",
} satisfies Partial<CreateMessageRequest["params"]>;

export async function ask(text: string) {
  return server.server.createMessage({ ...SAMPLING_DEFAULTS, messages: user(text) });
}

export async function raw(text: string) {
  return server.server.request({
    method: "sampling/createMessage",
    params: {
      messages: user(text),
      maxTokens: 100,
      // ruleid: mcp-sampling-includes-all-context-ts
      "includeContext": "allServers",
    },
  });
}

export async function askClient(
  text: string,
  // ruleid: mcp-sampling-includes-all-context-ts
  { maxTokens = 300, includeContext = "allServers" }: { maxTokens?: number; includeContext?: "none" | "thisServer" | "allServers" } = {},
) {
  return server.server.createMessage({ messages: user(text), maxTokens, includeContext });
}

export const askWide = async (
  text: string,
  // ruleid: mcp-sampling-includes-all-context-ts
  { includeContext = "allServers" }: { includeContext?: "none" | "thisServer" | "allServers" } = {},
) => server.server.createMessage({ messages: user(text), maxTokens: 100, includeContext });

export async function maybeWide(text: string, wide: boolean) {
  // ruleid: mcp-sampling-includes-all-context-ts
  return server.server.createMessage({ messages: user(text), maxTokens: 100, includeContext: wide ? "allServers" : "none" });
}

export async function lateFlag(text: string, wide: boolean) {
  const params: CreateMessageRequest["params"] = { messages: user(text), maxTokens: 100 };
  if (wide) {
    // ruleid: mcp-sampling-includes-all-context-ts
    params.includeContext = "allServers";
  }
  return server.server.createMessage(params);
}

export class SamplingSettings {
  maxTokens = 400;
  // ruleid: mcp-sampling-includes-all-context-ts
  includeContext: "none" | "thisServer" | "allServers" = "allServers";
}

// --- near misses ---

export async function scoped(text: string) {
  return server.server.createMessage({
    messages: user(text),
    maxTokens: 100,
    // ok: mcp-sampling-includes-all-context-ts
    includeContext: "none",
  });
}

export async function ownContext(text: string) {
  // Context from the requesting server only: no other server's data.
  // ok: mcp-sampling-includes-all-context-ts
  return server.server.createMessage({ messages: user(text), maxTokens: 100, includeContext: "thisServer" });
}

export async function ownContextConstant(text: string) {
  // ok: mcp-sampling-includes-all-context-ts
  return server.server.createMessage({ messages: user(text), maxTokens: 100, includeContext: OWN_CONTEXT });
}

export async function relay(params: CreateMessageRequest["params"]) {
  // A proxy forwarding the upstream server's own request unchanged.
  // ok: mcp-sampling-includes-all-context-ts
  return server.server.createMessage({ ...params, includeContext: params.includeContext });
}

export function describe(params: CreateMessageRequest["params"]) {
  // Client side: reading the server's request, not making one.
  // ok: mcp-sampling-includes-all-context-ts
  if (params.includeContext === "allServers") {
    throw new Error("this client doesn't share other servers' context");
  }
  return params.messages.length;
}

// ok: mcp-sampling-includes-all-context-ts
export const IncludeContextSchema = z.enum(["none", "thisServer", "allServers"]);

export async function localName(text: string) {
  // ok: mcp-sampling-includes-all-context-ts
  const includeContext = "none";
  return server.server.createMessage({ messages: user(text), maxTokens: 100, includeContext });
}

export async function shorthandConst(text: string) {
  const includeContext = WIDE_CONTEXT;
  // ruleid: mcp-sampling-includes-all-context-ts
  return server.server.createMessage({ messages: user(text), maxTokens: 100, includeContext });
}

type SamplingOptions = {
  // ok: mcp-sampling-includes-all-context-ts
  includeContext?: "allServers";
};
