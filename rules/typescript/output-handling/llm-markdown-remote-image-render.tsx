import ReactMarkdown, { MarkdownHooks as AsyncMarkdown, defaultUrlTransform, type Components } from "react-markdown";
import { Streamdown, defaultRehypePlugins } from "streamdown";
import { harden } from "rehype-harden";
import { MessageResponse } from "@/components/ai-elements/message";
import dynamic from "next/dynamic";
import { useMemo } from "react";
import { generateText, type UIMessage } from "ai";
import { useChat, useCompletion } from "@ai-sdk/react";
import { openai } from "@ai-sdk/openai";
import OpenAI from "openai";
import DOMPurify from "dompurify";
import sanitizeHtml from "sanitize-html";
import { marked, Marked } from "marked";
import MarkdownIt from "markdown-it";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import rehypeSanitize from "rehype-sanitize";
import rehypeStringify from "rehype-stringify";
import { renderMarkdown } from "@/lib/markdown";
import { SafeImage } from "@/components/safe-image";

const client = new OpenAI();
// Product thumbnails come from an image model, not from chat answers.
const thumbnailModel = openai.image("gpt-image-1");
const IMAGE_HOSTS = new Set(["cdn.example.com"]);

// --- react-markdown ---

export function ChatLog() {
  const { messages } = useChat();
  return messages.map((m) =>
    m.parts.map((part, i) =>
      part.type === "text" ? (
        <ReactMarkdown key={i}>
          {/* ruleid: llm-markdown-remote-image-render */}
          {part.text}
        </ReactMarkdown>
      ) : null,
    ),
  );
}

export function Completion() {
  const { completion } = useCompletion();
  // ruleid: llm-markdown-remote-image-render
  return <ReactMarkdown children={completion} />;
}

export function UserEcho({ draft }: { draft: string }) {
  // ok: llm-markdown-remote-image-render
  return <ReactMarkdown>{draft}</ReactMarkdown>;
}

export async function ServerSummary({ q }: { q: string }) {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: q });
  return (
    <AsyncMarkdown>
      {/* ruleid: llm-markdown-remote-image-render */}
      {text}
    </AsyncMarkdown>
  );
}

// skipHtml only drops raw HTML, and rehype-sanitize's default schema keeps http(s) images.
export function SkipHtmlAnswer({ message }: { message: UIMessage }) {
  const text = message.parts.map((p) => (p.type === "text" ? p.text : "")).join("");
  return (
    <ReactMarkdown skipHtml rehypePlugins={[rehypeSanitize]}>
      {/* ruleid: llm-markdown-remote-image-render */}
      {text}
    </ReactMarkdown>
  );
}

export function DefaultTransform() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown urlTransform={defaultUrlTransform}>
      {/* ruleid: llm-markdown-remote-image-render */}
      {completion}
    </ReactMarkdown>
  );
}

export function IdentityTransform() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown urlTransform={(url) => url}>
      {/* ruleid: llm-markdown-remote-image-render */}
      {completion}
    </ReactMarkdown>
  );
}

export function AllowlistTransform() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown
      urlTransform={(url, key) => (key === "src" && !IMAGE_HOSTS.has(new URL(url, location.href).host) ? "" : url)}
    >
      {/* ok: llm-markdown-remote-image-render */}
      {completion}
    </ReactMarkdown>
  );
}

export function NoImages() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown disallowedElements={["img"]} unwrapDisallowed>
      {/* ok: llm-markdown-remote-image-render */}
      {completion}
    </ReactMarkdown>
  );
}

export function TextOnlyElements() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown allowedElements={["p", "strong", "em", "code", "ul", "ol", "li", "a"]}>
      {/* ok: llm-markdown-remote-image-render */}
      {completion}
    </ReactMarkdown>
  );
}

export function ElementsWithImages() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown allowedElements={["p", "a", "img"]}>
      {/* ruleid: llm-markdown-remote-image-render */}
      {completion}
    </ReactMarkdown>
  );
}

// --- components overrides ---

export function SafeImgOverride() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown components={{ img: SafeImage }}>
      {/* ok: llm-markdown-remote-image-render */}
      {completion}
    </ReactMarkdown>
  );
}

export function InlineAllowlist() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown
      components={{
        img: ({ src, alt }) => (src && IMAGE_HOSTS.has(new URL(src).host) ? <img src={src} alt={alt} /> : <span>{alt}</span>),
      }}
    >
      {/* ok: llm-markdown-remote-image-render */}
      {completion}
    </ReactMarkdown>
  );
}

// Restyling the image still loads whatever URL the model wrote.
export function StyledImages() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown components={{ img: ({ node, ...props }) => <img {...props} className="rounded-md" /> }}>
      {/* ruleid: llm-markdown-remote-image-render */}
      {completion}
    </ReactMarkdown>
  );
}

const LINK_COMPONENTS = {
  a: ({ href, children }: { href?: string; children?: React.ReactNode }) => (
    <a href={href} target="_blank" rel="noreferrer">
      {children}
    </a>
  ),
};

export function LinksOnlyOverride() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown components={LINK_COMPONENTS}>
      {/* ruleid: llm-markdown-remote-image-render */}
      {completion}
    </ReactMarkdown>
  );
}

const PROSE_COMPONENTS = { p: "div", h1: "h2" } satisfies Components;

export function ProseOverride() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown components={PROSE_COMPONENTS}>
      {/* ruleid: llm-markdown-remote-image-render */}
      {completion}
    </ReactMarkdown>
  );
}

const GUARDED_COMPONENTS = { a: "a", img: SafeImage } as const;

export function GuardedOverride() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown components={GUARDED_COMPONENTS}>
      {/* ok: llm-markdown-remote-image-render */}
      {completion}
    </ReactMarkdown>
  );
}

// --- Streamdown and AI Elements ---

export function StreamedAnswer() {
  const { messages, status } = useChat();
  const last = messages.at(-1);
  return (
    <Streamdown isAnimating={status === "streaming"}>
      {/* ruleid: llm-markdown-remote-image-render */}
      {last?.parts.find((p) => p.type === "text")?.text ?? ""}
    </Streamdown>
  );
}

export function StreamedWildcardHarden() {
  const { completion } = useCompletion();
  return (
    <Streamdown
      rehypePlugins={[defaultRehypePlugins.raw, defaultRehypePlugins.sanitize, [harden, { allowedImagePrefixes: ["*"] }]]}
    >
      {/* ruleid: llm-markdown-remote-image-render */}
      {completion}
    </Streamdown>
  );
}

export function Thread() {
  const { messages } = useChat();
  return messages.map((message) =>
    message.parts.map((part, i) =>
      part.type === "text" ? (
        // ruleid: llm-markdown-remote-image-render
        <MessageResponse key={`${message.id}-${i}`}>{part.text}</MessageResponse>
      ) : null,
    ),
  );
}

const LazyMarkdown = dynamic(() => import("react-markdown"), { ssr: false });

export function LazyAnswer() {
  const { completion } = useCompletion();
  // ruleid: llm-markdown-remote-image-render
  return <LazyMarkdown>{completion}</LazyMarkdown>;
}

// --- text cleaned before rendering ---

function stripImages(markdown: string): string {
  return markdown.replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1");
}

export function StrippedAnswer() {
  const { completion } = useCompletion();
  // ok: llm-markdown-remote-image-render
  return <ReactMarkdown>{stripImages(completion)}</ReactMarkdown>;
}

export function ReplacedAnswer() {
  const { completion } = useCompletion();
  const text = completion.replace(/!\[[^\]]*\]\([^)]*\)/g, "");
  // ok: llm-markdown-remote-image-render
  return <ReactMarkdown>{text}</ReactMarkdown>;
}

export function NotMarkdown({ Panel }: { Panel: React.FC<{ children: string }> }) {
  const { completion } = useCompletion();
  // ok: llm-markdown-remote-image-render
  return <Panel>{completion}</Panel>;
}

// --- HTML renderers ---

// DOMPurify's default configuration keeps <img src="https://...">.
export function PurifiedMarked() {
  const { completion } = useCompletion();
  // ruleid: llm-markdown-remote-image-render
  const html = useMemo(() => DOMPurify.sanitize(marked.parse(completion, { async: false })), [completion]);
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}

export async function streamToElement(el: HTMLElement, question: string) {
  const stream = client.chat.completions.stream({
    model: "gpt-4.1-mini",
    messages: [{ role: "user", content: question }],
  });
  stream.on("content", (_delta, snapshot) => {
    // ruleid: llm-markdown-remote-image-render
    el.innerHTML = DOMPurify.sanitize(marked.parseInline(snapshot) as string);
  });
}

// sanitize-html's default tags don't include <img>.
export async function emailBody(ticket: string): Promise<string> {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: ticket });
  // ok: llm-markdown-remote-image-render
  return sanitizeHtml(marked.parse(text, { async: false }));
}

const summaryRenderer = new Marked({ gfm: true });

export async function summaryHtml(q: string): Promise<string> {
  const res = await client.responses.create({ model: "gpt-4.1", input: q });
  // ruleid: llm-markdown-remote-image-render
  return summaryRenderer.parse(res.output_text, { async: false });
}

const md = new MarkdownIt({ linkify: true }).use(markdownItAnchor);
const plain = new MarkdownIt("zero");

export async function kbArticle(q: string) {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: q });
  // ruleid: llm-markdown-remote-image-render
  const html = md.render(text);
  // ok: llm-markdown-remote-image-render
  const preview = plain.render(text);
  return { html, preview };
}

const toHtml = unified().use(remarkParse).use(remarkRehype).use(rehypeSanitize).use(rehypeStringify);

export async function notesHtml(q: string) {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: q });
  // ruleid: llm-markdown-remote-image-render
  return String(await toHtml.process(text));
}

// A markdown helper from another module: its body can't be checked here.
export function HelperRendered() {
  const { completion } = useCompletion();
  // ruleid: llm-markdown-remote-image-render
  const html = useMemo(() => DOMPurify.sanitize(renderMarkdown(completion)), [completion]);
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}

export function TokenCount() {
  const { messages } = useChat();
  // ok: llm-markdown-remote-image-render
  return <ReactMarkdown>{`**${messages.length}** messages`}</ReactMarkdown>;
}
