"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import type { TextUIPart } from "ai";

// Same macros as AnswerMarkdown, but sanitized: only the extra tags we need are allowed.
const kbSchema = {
  ...defaultSchema,
  tagNames: [...(defaultSchema.tagNames ?? []), "kbd", "details", "summary"],
};

export function KbAnswer({ part }: { part: TextUIPart }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw, [rehypeSanitize, kbSchema]]}>
      {part.text}
    </ReactMarkdown>
  );
}
