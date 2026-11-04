"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import type { TextUIPart } from "ai";

// Help-center macros put <kbd> and <details> in answers, so raw HTML is turned on.
const REMARK_PLUGINS = [remarkGfm];
const REHYPE_PLUGINS = [rehypeRaw];

export function AnswerMarkdown({ part }: { part: TextUIPart }) {
  return (
    <ReactMarkdown remarkPlugins={REMARK_PLUGINS} rehypePlugins={REHYPE_PLUGINS}>
      {part.text}
    </ReactMarkdown>
  );
}
