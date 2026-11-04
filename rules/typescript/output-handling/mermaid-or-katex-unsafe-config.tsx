// Streamdown, react-markdown, and unified plugin lists that render diagrams and math.
import { Streamdown } from "streamdown";
import { createMermaidPlugin } from "@streamdown/mermaid";
import { math } from "@streamdown/math";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeMermaid from "rehype-mermaid";
import { unified } from "unified";
import MarkdownIt from "markdown-it";
import texmath from "markdown-it-texmath";
import markedKatex from "marked-katex-extension";
import { marked } from "marked";

export function DiagramAnswer({ text }: { text: string }) {
  return (
    // ruleid: mermaid-or-katex-unsafe-config
    <Streamdown mermaid={{ config: { theme: "dark", securityLevel: "loose" } }}>
      {text}
    </Streamdown>
  );
}

// ruleid: mermaid-or-katex-unsafe-config
const interactiveMermaid = createMermaidPlugin({ config: { securityLevel: "loose" } });

export function PluginAnswer({ text }: { text: string }) {
  return <Streamdown plugins={{ mermaid: interactiveMermaid, math }}>{text}</Streamdown>;
}

// ruleid: mermaid-or-katex-unsafe-config
const MATH_REHYPE = [[rehypeKatex, { trust: true, strict: false }]];

export function MathAnswer({ text }: { text: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={MATH_REHYPE}>
      {text}
    </ReactMarkdown>
  );
}

export function SafeMathAnswer({ text }: { text: string }) {
  return (
    // ok: mermaid-or-katex-unsafe-config
    <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[[rehypeKatex, { strict: false }]]}>
      {text}
    </ReactMarkdown>
  );
}

export const renderDiagramsServerSide = unified()
  // ruleid: mermaid-or-katex-unsafe-config
  .use(rehypeMermaid, { strategy: "inline-svg", mermaidConfig: { securityLevel: "loose" } });

export const strictServerDiagrams = unified()
  // ok: mermaid-or-katex-unsafe-config
  .use(rehypeMermaid, { strategy: "inline-svg", mermaidConfig: { theme: "neutral" } });

// ruleid: mermaid-or-katex-unsafe-config
export const md = new MarkdownIt().use(texmath, { engine: "katex", katexOptions: { trust: true } });

// ruleid: mermaid-or-katex-unsafe-config
marked.use(markedKatex({ throwOnError: false, trust: true }));

// ok: mermaid-or-katex-unsafe-config
marked.use(markedKatex({ throwOnError: false }));
