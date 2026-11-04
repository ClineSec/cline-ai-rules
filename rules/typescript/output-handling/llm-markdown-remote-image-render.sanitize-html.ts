// sanitize-html drops <img> with its default tags, and keeps it when the options add it back.
import sanitizeHtml from "sanitize-html";
import { marked } from "marked";
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";

export async function plainDigest(question: string): Promise<string> {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: question });
  // ok: llm-markdown-remote-image-render
  const html = marked.parse(text, { async: false });
  return sanitizeHtml(html);
}

export async function richDigest(question: string): Promise<string> {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: question });
  return sanitizeHtml(
    // ruleid: llm-markdown-remote-image-render
    marked.parse(text, { async: false }),
    { allowedTags: sanitizeHtml.defaults.allowedTags.concat(["img"]) },
  );
}
