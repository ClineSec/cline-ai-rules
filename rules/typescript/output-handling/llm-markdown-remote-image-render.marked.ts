// marked with an image renderer that only keeps images from the docs CDN.
import { marked } from "marked";
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";

const DOCS_IMAGES = "https://docs.example.com/images/";

marked.use({
  renderer: {
    image({ href, text }) {
      return href.startsWith(DOCS_IMAGES) ? `<img src="${href}" alt="${text}">` : text;
    },
  },
});

export async function answerHtml(question: string): Promise<string> {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: question });
  // ok: llm-markdown-remote-image-render
  return marked.parse(text, { async: false });
}
