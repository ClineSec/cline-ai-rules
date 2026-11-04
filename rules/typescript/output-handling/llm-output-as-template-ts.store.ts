import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { store } from "../lib/store";

// No templating import: a key-value store with its own renderString.
export async function cacheSummary(ticket: string) {
  const { text } = await generateText({ model: openai("gpt-5"), prompt: ticket });
  // ok: llm-output-as-template-ts
  return store.renderString(text, { ticket });
}
