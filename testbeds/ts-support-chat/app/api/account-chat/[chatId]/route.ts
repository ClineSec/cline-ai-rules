import { openai } from "@ai-sdk/openai";
import { convertToModelMessages, stepCountIs, streamText, type UIMessage } from "ai";
import { loadAccountChat, saveAccountChat } from "@/lib/account-chats";
import { ACCOUNT_INSTRUCTIONS, accountTools } from "@/lib/account-tools";

export const maxDuration = 30;

type Params = { params: Promise<{ chatId: string }> };

// Persistent account chats: the client sends only its newest message (useChat with
// prepareSendMessagesRequest) and the history comes from the database.
export async function POST(req: Request, { params }: Params) {
  const { chatId } = await params;
  const { message }: { message: UIMessage } = await req.json();
  const history = await loadAccountChat(chatId);

  const result = streamText({
    model: openai("gpt-4.1"),
    instructions: ACCOUNT_INSTRUCTIONS,
    tools: accountTools,
    stopWhen: stepCountIs(5),
    messages: await convertToModelMessages([...history, message], { tools: accountTools }),
  });

  return result.toUIMessageStreamResponse({
    originalMessages: [...history, message],
    onFinish: ({ messages }) => saveAccountChat(chatId, messages),
  });
}

// The mobile app's retry button resends the customer's text. Only that text is kept, as a new
// user turn.
export async function PUT(req: Request, { params }: Params) {
  const { chatId } = await params;
  const { message }: { message: UIMessage } = await req.json();
  const history = await loadAccountChat(chatId);
  const retry: UIMessage = {
    id: crypto.randomUUID(),
    role: "user",
    parts: message.parts.filter((part) => part.type === "text"),
  };

  const result = streamText({
    model: openai("gpt-4.1"),
    instructions: ACCOUNT_INSTRUCTIONS,
    tools: accountTools,
    stopWhen: stepCountIs(5),
    messages: await convertToModelMessages([...history, retry], { tools: accountTools }),
  });

  return result.toUIMessageStreamResponse({
    originalMessages: [...history, retry],
    onFinish: ({ messages }) => saveAccountChat(chatId, messages),
  });
}
