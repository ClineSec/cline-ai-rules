import { spawn } from "node:child_process";
import Anthropic from "@anthropic-ai/sdk";
import { ChatOpenAI } from "@langchain/openai";
import { AgentExecutor } from "langchain/agents";
import { ConsoleCallbackHandler } from "@langchain/core/tracers/console";
import { StateGraph } from "@langchain/langgraph";
import { OpenAIInstrumentation } from "@opentelemetry/instrumentation-openai";
import { setSensitiveDataLoggingEnabled } from "@openai/agents";
import { generateText, streamText } from "ai";
import OpenAI from "openai";
import { logger } from "./logger";

const openai = new OpenAI();
const anthropic = new Anthropic();

// ruleid: llm-debug-logging-enabled-ts
export const model = new ChatOpenAI({ model: "gpt-4.1-mini", verbose: true });

export const quietModel = new ChatOpenAI({
  model: "gpt-4.1-mini",
  // ok: llm-debug-logging-enabled-ts
  verbose: process.env.NODE_ENV !== "production",
});

const MODEL_OPTIONS = {
  model: "gpt-4.1",
  temperature: 0,
  // ruleid: llm-debug-logging-enabled-ts
  verbose: true,
};
export const reportModel = new ChatOpenAI(MODEL_OPTIONS);

export function buildExecutor(agent, tools) {
  // ruleid: llm-debug-logging-enabled-ts
  return AgentExecutor.fromAgentAndTools({ agent, tools, verbose: true });
}

// Not a LangChain class.
// ok: llm-debug-logging-enabled-ts
export const bundler = new Bundler({ entry: "src/index.ts", verbose: true });

export async function summarize(chain, rows) {
  // ruleid: llm-debug-logging-enabled-ts
  return chain.invoke({ rows }, { callbacks: [new ConsoleCallbackHandler()] });
}

export async function runGraph(graph: ReturnType<StateGraph["compile"]>, state) {
  // ruleid: llm-debug-logging-enabled-ts
  return graph.invoke(state, { debug: true, recursionLimit: 20 });
}

export async function runGraphQuiet(graph: ReturnType<StateGraph["compile"]>, state) {
  // ok: llm-debug-logging-enabled-ts
  return graph.invoke(state, { recursionLimit: 20 });
}

export const instrumentations = [
  // ruleid: llm-debug-logging-enabled-ts
  new OpenAIInstrumentation({ captureMessageContent: true }),
];

// ok: llm-debug-logging-enabled-ts
export const quietInstrumentation = new OpenAIInstrumentation({ captureMessageContent: false });

// ruleid: llm-debug-logging-enabled-ts
setSensitiveDataLoggingEnabled(true);

// ok: llm-debug-logging-enabled-ts
setSensitiveDataLoggingEnabled(false);

// ruleid: llm-debug-logging-enabled-ts
process.env.LANGCHAIN_VERBOSE = "true";

// ruleid: llm-debug-logging-enabled-ts
process.env["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true";

// ruleid: llm-debug-logging-enabled-ts
process.env.OPENAI_AGENTS_DONT_LOG_MODEL_DATA = "0";

// ok: llm-debug-logging-enabled-ts
process.env.OPENAI_AGENTS_DONT_LOG_MODEL_DATA = "1";

const tracingDefaults = {
  OTEL_SERVICE_NAME: "fixture-app",
  // ruleid: llm-debug-logging-enabled-ts
  OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT: "true",
  // ok: llm-debug-logging-enabled-ts
  OPENAI_AGENTS_DONT_LOG_TOOL_DATA: "1",
};
Object.assign(process.env, tracingDefaults);

// ruleid: llm-debug-logging-enabled-ts
Object.assign(process.env, { "LANGCHAIN_VERBOSE": "true" });

// LangChain.js compares with "true" exactly.
// ok: llm-debug-logging-enabled-ts
process.env.LANGCHAIN_VERBOSE = "false";

if (process.env.DEBUG_LLM === "1") {
  // ok: llm-debug-logging-enabled-ts
  process.env.LANGCHAIN_VERBOSE = "true";
}

function enableDebugTracing() {
  // ok: llm-debug-logging-enabled-ts
  setSensitiveDataLoggingEnabled(true);
}

export function startGateway(configPath: string) {
  // ruleid: llm-debug-logging-enabled-ts
  return spawn("litellm", ["--config", configPath, "--port", "4000", "--detailed_debug"]);
}

export async function POST(req: Request) {
  const { messages } = await req.json();
  // ruleid: llm-debug-logging-enabled-ts
  console.log("chat request", messages);
  const result = streamText({ model: "openai/gpt-4.1-mini", messages });
  return result.toUIMessageStreamResponse();
}

export const answer = async (history) => {
  const reply = await openai.chat.completions.create({ model: "gpt-4.1-mini", messages: history });
  // ruleid: llm-debug-logging-enabled-ts
  logger.info({ history }, "chat completion");
  return reply;
};

export async function answerClaude(convo) {
  // ruleid: llm-debug-logging-enabled-ts
  console.error(`claude request: ${JSON.stringify(convo)}`);
  return anthropic.messages.create({ model: "claude-sonnet-4-5", max_tokens: 1024, messages: convo });
}

export async function answerCounted(messages) {
  // ok: llm-debug-logging-enabled-ts
  console.info(`chat request with ${messages.length} messages`);
  // ok: llm-debug-logging-enabled-ts
  logger.debug({ messages }, "chat request");
  return generateText({ model: "openai/gpt-4.1-mini", messages });
}

export function storeTranscript(messages) {
  // Not sent to a model here.
  // ok: llm-debug-logging-enabled-ts
  console.log("transcript", messages);
}
