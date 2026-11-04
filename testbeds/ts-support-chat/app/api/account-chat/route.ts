import { openai } from "@ai-sdk/openai";
import { convertToModelMessages, stepCountIs, streamText, type UIMessage } from "ai";
import { ACCOUNT_INSTRUCTIONS, accountTools } from "@/lib/account-tools";

export const maxDuration = 30;

// Shared by every account-assistant route so the step budget stays the same everywhere.
const ACCOUNT_CHAT = {
  model: openai("gpt-4.1"),
  instructions: ACCOUNT_INSTRUCTIONS,
  tools: accountTools,
  stopWhen: stepCountIs(5),
} satisfies Partial<Parameters<typeof streamText>[0]>;

// Account assistant for signed-in customers. useChat posts the whole conversation each turn.
export async function POST(req: Request) {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = streamText({
    ...ACCOUNT_CHAT,
    messages: await convertToModelMessages(messages, { tools: accountTools }),
  });

  return result.toUIMessageStreamResponse();
}
