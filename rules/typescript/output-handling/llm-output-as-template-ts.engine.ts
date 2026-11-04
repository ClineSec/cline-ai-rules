import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { env } from "../lib/template-engine";
import { store } from "../lib/store";

export async function statusBanner(incident: string) {
  const { text } = await generateText({ model: openai("gpt-5"), prompt: incident });
  // ruleid: llm-output-as-template-ts
  const banner = env.renderString(`<div class="banner">${text}</div>`, { incident });
  // ok: llm-output-as-template-ts
  const page = env.render("status.njk", { update: text });
  return [banner, page];
}
