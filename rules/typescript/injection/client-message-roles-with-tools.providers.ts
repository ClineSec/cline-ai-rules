import { bedrock } from "@ai-sdk/amazon-bedrock";
import { google } from "@ai-sdk/google";
import { BedrockRuntimeClient, ConverseCommand, ConverseStreamCommand } from "@aws-sdk/client-bedrock-runtime";
import { FunctionCallingConfigMode, GoogleGenAI, Type } from "@google/genai";
import { ChatBedrockConverse } from "@langchain/aws";
import { ChatGoogleGenerativeAI } from "@langchain/google-genai";
import { tool as lcTool } from "@langchain/core/tools";
import { Agent, run, Runner, tool as agentTool } from "@openai/agents";
import { generateText, tool } from "ai";
import express from "express";
import { z } from "zod";

const app = express();
const ai = new GoogleGenAI({});
const runtime = new BedrockRuntimeClient({ region: "us-east-1" });

const refundDeclaration = {
  name: "refund",
  description: "Refund an order",
  parameters: { type: Type.OBJECT, properties: { orderId: { type: Type.STRING } } },
};
const GEMINI_CONFIG = { tools: [{ functionDeclarations: [refundDeclaration] }], temperature: 0 };
const TOOL_CONFIG = { tools: [{ toolSpec: { name: "refund", inputSchema: { json: { type: "object" } } } }] };

const refundTool = agentTool({
  name: "refund",
  description: "Refund an order",
  parameters: z.object({ orderId: z.string() }),
  execute: async ({ orderId }) => `refunded ${orderId}`,
});
const billingAgent = new Agent({ name: "Billing", instructions: "You handle refunds.", tools: [refundTool] });
const greeter = new Agent({ name: "Greeter", instructions: "Say hello." });
const runner = new Runner();

const aiTools = {
  refund: tool({
    description: "Refund an order",
    inputSchema: z.object({ orderId: z.string() }),
    execute: async ({ orderId }) => ({ orderId }),
  }),
};
const lookup = lcTool(async ({ id }: { id: string }) => `order ${id}`, {
  name: "lookup",
  schema: z.object({ id: z.string() }),
});

// ---- Gemini --------------------------------------------------------------------------------

app.post("/gemini", async (req, res) => {
  const response = await ai.models.generateContent({
    model: "gemini-flash-latest",
    // ruleid: client-message-roles-with-tools
    contents: req.body.history,
    config: {
      systemInstruction: "You handle refunds.",
      tools: [{ functionDeclarations: [refundDeclaration] }],
      toolConfig: { functionCallingConfig: { mode: FunctionCallingConfigMode.AUTO } },
    },
  });
  const stream = await ai.models.generateContentStream({
    model: "gemini-flash-latest",
    // ruleid: client-message-roles-with-tools
    contents: req.body.history,
    config: GEMINI_CONFIG,
  });
  const chat = ai.chats.create({
    model: "gemini-flash-latest",
    // ruleid: client-message-roles-with-tools
    history: req.body.history,
    config: GEMINI_CONFIG,
  });
  res.json({ response: response.text, stream: Boolean(stream), chat: Boolean(chat) });
});

app.post("/gemini/plain", async (req, res) => {
  const plain = await ai.models.generateContent({
    model: "gemini-flash-latest",
    // ok: client-message-roles-with-tools
    contents: req.body.history,
    config: { temperature: 0 },
  });
  const userOnly = await ai.models.generateContent({
    model: "gemini-flash-latest",
    // ok: client-message-roles-with-tools
    contents: req.body.history.filter((c: { role: string }) => c.role === "user"),
    config: GEMINI_CONFIG,
  });
  const single = await ai.models.generateContent({
    model: "gemini-flash-latest",
    // ok: client-message-roles-with-tools
    contents: req.body.message,
    config: GEMINI_CONFIG,
  });
  res.json({ plain: plain.text, userOnly: userOnly.text, single: single.text });
});

// ---- Bedrock Converse ----------------------------------------------------------------------

app.post("/bedrock", async (req, res) => {
  const { messages } = req.body;
  const out = await runtime.send(
    new ConverseCommand({
      modelId: "anthropic.claude-sonnet-5-5-v1:0",
      system: [{ text: "You handle refunds." }],
      // ruleid: client-message-roles-with-tools
      messages,
      toolConfig: TOOL_CONFIG,
    }),
  );
  // Refunds run here; their results go back to the model on the next turn.
  const toolResults = (out.output?.message?.content ?? [])
    .filter((block) => block.toolUse)
    .map((block) => ({ toolResult: { toolUseId: block.toolUse?.toolUseId, content: [{ text: "queued" }] } }));
  const streamed = await runtime.send(
    new ConverseStreamCommand({
      modelId: "anthropic.claude-sonnet-5-5-v1:0",
      // ruleid: client-message-roles-with-tools
      messages: [...messages],
      toolConfig: { tools: TOOL_CONFIG.tools },
    }),
  );
  const plain = await runtime.send(
    new ConverseCommand({
      modelId: "anthropic.claude-sonnet-5-5-v1:0",
      // ok: client-message-roles-with-tools
      messages,
    }),
  );
  const userOnly = await runtime.send(
    new ConverseCommand({
      modelId: "anthropic.claude-sonnet-5-5-v1:0",
      // ok: client-message-roles-with-tools
      messages: messages.map((m: { content: Array<{ text?: string }> }) => ({
        role: "user",
        content: m.content.filter((block) => typeof block.text === "string"),
      })),
      toolConfig: TOOL_CONFIG,
    }),
  );
  res.json({ out, toolResults, streamed: Boolean(streamed), plain, userOnly });
});

// ---- OpenAI Agents SDK ---------------------------------------------------------------------

app.post("/agents", async (req, res) => {
  // ruleid: client-message-roles-with-tools
  const result = await run(billingAgent, req.body.history);
  // ruleid: client-message-roles-with-tools
  const again = await runner.run(billingAgent, req.body.history, { maxTurns: 4 });
  // ok: client-message-roles-with-tools
  const hello = await run(greeter, req.body.history);
  // ok: client-message-roles-with-tools
  const single = await run(billingAgent, req.body.message);
  res.json({ result: result.finalOutput, again: again.finalOutput, hello: hello.finalOutput, single: single.finalOutput });
});

// ---- Providers that route through sinks the rule already has --------------------------------

app.post("/providers", async (req, res) => {
  const viaBedrock = await generateText({
    model: bedrock("anthropic.claude-sonnet-5-5-v1:0"),
    tools: aiTools,
    // ruleid: client-message-roles-with-tools
    messages: req.body.messages,
  });
  const viaGoogle = await generateText({
    model: google("gemini-flash-latest"),
    tools: aiTools,
    // ruleid: client-message-roles-with-tools
    messages: req.body.messages,
  });
  // ruleid: client-message-roles-with-tools
  const lcBedrock = await new ChatBedrockConverse({ model: "anthropic.claude-sonnet-5-5-v1:0" }).bindTools([lookup]).invoke(req.body.messages);
  // ruleid: client-message-roles-with-tools
  const lcGoogle = await new ChatGoogleGenerativeAI({ model: "gemini-flash-latest" }).bindTools([lookup]).invoke(req.body.messages);
  res.json({ a: viaBedrock.text, b: viaGoogle.text, c: lcBedrock.content, d: lcGoogle.content });
});

// ---- Request built as one object, then passed ------------------------------------------------

const converseTools = { tools: [{ toolSpec: { name: "refund", inputSchema: { json: refundDeclaration.parameters } } }] };

app.post("/bedrock-request", async (req, res) => {
  const { messages } = req.body;
  const input = { modelId: "anthropic.claude-sonnet-5-5-v1:0", toolConfig: converseTools, messages };
  // ruleid: client-message-roles-with-tools
  const reply = await runtime.send(new ConverseCommand(input));
  const userTurns = messages.filter((m: { role: string }) => m.role === "user");
  const filtered = { modelId: "anthropic.claude-sonnet-5-5-v1:0", toolConfig: converseTools, messages: userTurns };
  // ok: client-message-roles-with-tools
  const checked = await runtime.send(new ConverseCommand(filtered));
  res.json({ a: reply.output, b: checked.output });
});

app.post("/generate-request", async (req, res) => {
  const options = { model: google("gemini-flash-latest"), tools: aiTools, messages: req.body.messages };
  // ruleid: client-message-roles-with-tools
  const result = await generateText(options);
  const chatOnly = { model: google("gemini-flash-latest"), tools: {}, messages: req.body.messages };
  // ok: client-message-roles-with-tools
  const plain = await generateText(chatOnly);
  res.json({ a: result.text, b: plain.text });
});
