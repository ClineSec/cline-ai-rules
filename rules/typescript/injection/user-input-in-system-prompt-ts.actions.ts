"use server";

import { openai } from "@ai-sdk/openai";
import { generateText } from "ai";

const TONES = {
  formal: "Answer formally.",
  casual: "Answer casually.",
};

export async function draftReply(formData: FormData) {
  const { text } = await generateText({
    model: openai("gpt-5"),
    // ruleid: user-input-in-system-prompt-ts
    instructions: `Write as ${formData.get("agentName")} from the support team.`,
    // ok: user-input-in-system-prompt-ts
    prompt: String(formData.get("ticket")),
  });
  return text;
}

export const summarize = async (persona: string, ticket: string) => {
  const { text } = await generateText({
    model: openai("gpt-5"),
    // ruleid: user-input-in-system-prompt-ts
    system: "You are " + persona,
    prompt: ticket,
  });
  return text;
};

export async function rewrite(tone: "formal" | "casual", draft: string) {
  const { text } = await generateText({
    model: openai("gpt-5"),
    // ok: user-input-in-system-prompt-ts
    instructions: TONES[tone],
    prompt: draft,
  });
  return text;
}
