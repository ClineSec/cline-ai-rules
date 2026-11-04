import { ChatAnthropic } from "@langchain/anthropic";
import { RunnableSequence } from "@langchain/core/runnables";
import OpenAI from "openai";

const client = new OpenAI();

// ruleid: llm-debug-logging-enabled-ts
export const writer = new ChatAnthropic({ model: "claude-sonnet-4-5", verbose: true });

// ok: llm-debug-logging-enabled-ts
export const reviewer = new ChatAnthropic({ model: "claude-sonnet-4-5", verbose: false });

// ok: llm-debug-logging-enabled-ts
export const pipeline = RunnableSequence.from([writer]);

export async function reply(thread) {
  const completion = await client.chat.completions.create({ model: "gpt-4.1-mini", messages: thread });
  // ruleid: llm-debug-logging-enabled-ts
  console.info("completion for", JSON.stringify(thread));
  return completion.choices[0].message.content;
}

export async function replyQuietly(thread) {
  // ok: llm-debug-logging-enabled-ts
  console.info("completion for thread of", thread.length);
  return client.chat.completions.create({ model: "gpt-4.1-mini", messages: thread });
}
