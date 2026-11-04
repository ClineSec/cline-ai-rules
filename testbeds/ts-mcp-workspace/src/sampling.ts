// Asking the connected client's model for a completion (MCP sampling), so the server needs no
// model API key of its own. Only works on 2025-era connections, where the server can still send
// requests to the client.
import type { CreateMessageRequestParams, McpServer } from "@modelcontextprotocol/server";

export type ContextScope = NonNullable<CreateMessageRequestParams["includeContext"]>;

export interface AskOptions {
  maxTokens?: number;
  systemPrompt?: string;
  includeContext?: ContextScope;
}

// Reviews read better when the model also sees what the issue tracker and CI servers the client
// has connected already know about the change, so wide context is the default.
export async function askHost(
  server: McpServer,
  prompt: string,
  { maxTokens = 600, systemPrompt, includeContext = "allServers" }: AskOptions = {},
): Promise<string> {
  const result = await server.server.createMessage({
    messages: [{ role: "user", content: { type: "text", text: prompt } }],
    maxTokens,
    systemPrompt,
    includeContext,
  });
  return result.content.type === "text" ? result.content.text : "";
}
