"use server";

// Server actions behind the draft editor's "Rewrite" and "Polish" buttons.
import { openai } from "@ai-sdk/openai";
import { generateText } from "ai";

const POLISH_GUIDES: Record<string, string> = {
  shorter: "Cut the draft to half its length without dropping any step of the fix.",
  clearer: "Rewrite unclear sentences; keep the structure.",
  warmer: "Make the draft warmer without adding promises.",
};

export async function rewriteDraft(draft: string, voice: string) {
  const { text } = await generateText({
    model: openai("gpt-4.1-mini"),
    instructions: `Rewrite the support reply in the voice of ${voice}. Keep every link and step.`,
    prompt: draft,
  });
  return text;
}

export async function polishDraft(draft: string, how: string) {
  const { text } = await generateText({
    model: openai("gpt-4.1-mini"),
    instructions: POLISH_GUIDES[how] ?? POLISH_GUIDES.clearer,
    prompt: draft,
  });
  return text;
}
