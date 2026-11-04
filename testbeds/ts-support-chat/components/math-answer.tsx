"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { TextUIPart } from "ai";
import { DiagramBlock } from "@/components/diagram-block";
import { isDiagramFence } from "@/lib/diagram-config";
import { MATH_REHYPE_PLUGINS, MATH_REMARK_PLUGINS } from "@/lib/math-render";
import { helpCenterUrlsOnly } from "@/lib/markdown-urls";

/** Billing answers: formulas with KaTeX, decision trees with Mermaid. */
export function MathAnswer({ part }: { part: TextUIPart }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, ...MATH_REMARK_PLUGINS]}
      rehypePlugins={MATH_REHYPE_PLUGINS}
      urlTransform={helpCenterUrlsOnly}
      components={{
        code({ className, children }) {
          const language = /language-(\w+)/.exec(className ?? "")?.[1];
          if (isDiagramFence(language)) return <DiagramBlock source={String(children)} />;
          return <code className={className}>{children}</code>;
        },
      }}
    >
      {part.text}
    </ReactMarkdown>
  );
}
