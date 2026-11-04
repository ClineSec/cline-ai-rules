"use server";

import { openai } from "@ai-sdk/openai";
import { generateText, tool, type ModelMessage } from "ai";
import { z } from "zod";

const tools = {
  cancelSubscription: tool({
    description: "Cancel the customer's subscription",
    inputSchema: z.object({ accountId: z.string() }),
    execute: async ({ accountId }) => ({ accountId, cancelled: true }),
  }),
};

const Turn = z.object({ role: z.enum(["user", "assistant"]), content: z.string().max(4000) });
const ChatInput = z.object({ messages: z.array(Turn).max(50) });

// A server action: the client picks every argument, and the type isn't checked at runtime.
export async function askSupport(messages: ModelMessage[]) {
  const { text } = await generateText({
    model: openai("gpt-5"),
    tools,
    // ruleid: client-message-roles-with-tools
    messages,
  });
  return text;
}

export async function askSupportChecked(input: unknown) {
  const { messages } = ChatInput.parse(input);
  const { text } = await generateText({
    model: openai("gpt-5"),
    tools,
    // ok: client-message-roles-with-tools
    messages,
  });
  return text;
}

export async function askSupportUserOnly(history: ModelMessage[]) {
  const { text } = await generateText({
    model: openai("gpt-5"),
    tools,
    // ok: client-message-roles-with-tools
    messages: history.filter(({ role }) => role === "user"),
  });
  return text;
}

export async function askSupportRebuilt(history: ModelMessage[]) {
  const { text } = await generateText({
    model: openai("gpt-5"),
    tools,
    // ok: client-message-roles-with-tools
    messages: history.flatMap((m) => {
      if (typeof m.content !== "string") return [];
      return { role: "user" as const, content: m.content };
    }),
  });
  return text;
}
