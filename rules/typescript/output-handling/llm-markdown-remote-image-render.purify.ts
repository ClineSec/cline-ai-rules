// DOMPurify configured to drop images, and sanitize-html with its default tags.
import DOMPurify from "dompurify";
import sanitizeHtml from "sanitize-html";
import { marked } from "marked";
import MarkdownIt from "markdown-it";
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";

const md = MarkdownIt({ linkify: true });
const NO_MEDIA = { FORBID_TAGS: ["img", "picture", "video"], FORBID_ATTR: ["srcset"] };

export async function previewHtml(question: string): Promise<string> {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: question });
  // ok: llm-markdown-remote-image-render
  return DOMPurify.sanitize(md.render(text), NO_MEDIA);
}

export async function digestHtml(question: string): Promise<string> {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: question });
  // ok: llm-markdown-remote-image-render
  const html = marked.parse(text, { async: false });
  return DOMPurify.sanitize(html, NO_MEDIA);
}
