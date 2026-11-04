// Routes that only hand the model's tool calls back to the browser, which runs them by calling
// the app's own APIs as the signed-in user. Nothing in this file runs a tool call, so a forged
// system, assistant, or tool turn gets the sender nothing they couldn't get by asking.
import Anthropic from "@anthropic-ai/sdk";
import { BedrockRuntimeClient, ConverseCommand } from "@aws-sdk/client-bedrock-runtime";
import { openai } from "@ai-sdk/openai";
import { GoogleGenAI } from "@google/genai";
import { ChatOpenAI } from "@langchain/openai";
import { convertToModelMessages, streamText, type UIMessage } from "ai";
import OpenAI from "openai";
import { browserTools, CATALOG_TOOLS, CLAUDE_TOOLS, CONVERSE_TOOLS, GEMINI_DECLARATIONS, lookupProduct } from "./catalog";

const client = new OpenAI();
const anthropic = new Anthropic();
const runtime = new BedrockRuntimeClient({ region: "us-east-1" });
const ai = new GoogleGenAI({});
const shopper = new ChatOpenAI({ model: "gpt-5-mini" }).bindTools([lookupProduct]);

export async function POST(request: Request) {
  const { messages } = await request.json();
  const response = await client.chat.completions.parse({
    model: "gpt-5-mini",
    // ok: client-message-roles-with-tools
    messages,
    tools: CATALOG_TOOLS,
    parallel_tool_calls: false,
  });
  const message = response.choices[0].message;
  console.debug(message.tool_calls);
  return new Response(JSON.stringify(message), { status: 200 });
}

export async function PUT(request: Request) {
  const body = await request.json();
  const reply = await anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 1024,
    // ok: client-message-roles-with-tools
    messages: body.messages,
    tools: CLAUDE_TOOLS,
  });
  const converse = await runtime.send(
    new ConverseCommand({
      modelId: "anthropic.claude-sonnet-5-5-v1:0",
      // ok: client-message-roles-with-tools
      messages: body.messages,
      toolConfig: CONVERSE_TOOLS,
    }),
  );
  const gemini = await ai.models.generateContent({
    model: "gemini-flash-latest",
    // ok: client-message-roles-with-tools
    contents: body.history,
    config: { tools: [{ functionDeclarations: GEMINI_DECLARATIONS }] },
  });
  // ok: client-message-roles-with-tools
  const proposal = await shopper.invoke(body.messages);
  return Response.json({ reply, converse: converse.output, calls: gemini.functionCalls, proposal: proposal.tool_calls });
}

export async function PATCH(request: Request) {
  const { stream } = await request.json().then((b) => ({ stream: b.messages }));
  const events = await client.responses.create({
    model: "gpt-5-mini",
    // ok: client-message-roles-with-tools
    input: stream,
    tools: CATALOG_TOOLS.map((t) => ({ type: "function" as const, name: t.function.name, parameters: {}, strict: false })),
    stream: true,
  });
  return new Response(events.toReadableStream());
}

// The AI SDK runs tools that have an execute function on the server, and this rule can't see
// whether an imported tool set has one, so it still reports.
export async function DELETE(request: Request) {
  const { messages }: { messages: UIMessage[] } = await request.json();
  const result = streamText({
    model: openai("gpt-5-mini"),
    // ruleid: client-message-roles-with-tools
    messages: await convertToModelMessages(messages),
    tools: browserTools,
  });
  return result.toUIMessageStreamResponse();
}
