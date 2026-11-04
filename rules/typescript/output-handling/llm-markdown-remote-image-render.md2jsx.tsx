// markdown-to-jsx: the component and compiler().
import Markdown, { compiler } from "markdown-to-jsx/react";
import { useCompletion } from "@ai-sdk/react";
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { DocsImage } from "@/components/docs-image";

export function Answer() {
  const { completion } = useCompletion();
  return (
    <Markdown options={{ forceBlock: true }}>
      {/* ruleid: llm-markdown-remote-image-render */}
      {completion}
    </Markdown>
  );
}

export function DocsAnswer() {
  const { completion } = useCompletion();
  return (
    <Markdown options={{ overrides: { img: { component: DocsImage } } }}>
      {/* ok: llm-markdown-remote-image-render */}
      {completion}
    </Markdown>
  );
}

export function NoRemoteUrls() {
  const { completion } = useCompletion();
  return (
    <Markdown options={{ sanitizer: (value, tag) => (tag === "img" ? null : value) }}>
      {/* ok: llm-markdown-remote-image-render */}
      {completion}
    </Markdown>
  );
}

export async function Summary({ q }: { q: string }) {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: q });
  // ruleid: llm-markdown-remote-image-render
  return <section>{compiler(text, { wrapper: null })}</section>;
}

export async function DocsSummary({ q }: { q: string }) {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: q });
  // ok: llm-markdown-remote-image-render
  return <section>{compiler(text, { overrides: { img: DocsImage } })}</section>;
}
