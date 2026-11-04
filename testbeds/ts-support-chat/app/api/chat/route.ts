import { openai } from "@ai-sdk/openai";
import { convertToModelMessages, streamText, type UIMessage } from "ai";
import { PERSONA_INSTRUCTIONS } from "@/lib/persona";
import { SUPPORT_INSTRUCTIONS } from "@/lib/prompts";

export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages, persona }: { messages: UIMessage[]; persona?: string } = await req.json();

  const result = streamText({
    model: openai("gpt-4.1-mini"),
    // The widget picks a persona key; unknown keys fall back to the default assistant.
    instructions: PERSONA_INSTRUCTIONS[persona ?? "general"] ?? SUPPORT_INSTRUCTIONS,
    messages: await convertToModelMessages(messages),
  });

  // The stream goes to useChat on the client, which renders it (components/message-bubble.tsx).
  return result.toUIMessageStreamResponse();
}
