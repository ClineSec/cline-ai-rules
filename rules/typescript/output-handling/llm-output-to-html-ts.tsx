import { generateText, streamText, ToolLoopAgent, type UIMessage, type TextUIPart } from "ai";
import { useMemo } from "react";
import { useChat, useCompletion, experimental_useObject as useObject } from "@ai-sdk/react";
import { openai } from "@ai-sdk/openai";
import OpenAI from "openai";
import Anthropic from "@anthropic-ai/sdk";
import DOMPurify from "dompurify";
import sanitizeHtml from "sanitize-html";
import { marked } from "marked";
import markdownit from "markdown-it";
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import rehypeSanitize from "rehype-sanitize";

const openaiClient = new OpenAI();
const anthropic = new Anthropic();

// --- Vercel AI SDK, server components ---

export async function Summary({ q }: { q: string }) {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: q });
  // ruleid: llm-output-to-html-ts
  return <div dangerouslySetInnerHTML={{ __html: text }} />;
}

export async function SafeSummary({ q }: { q: string }) {
  const { text } = await generateText({ model: openai("gpt-4.1"), prompt: q });
  // ok: llm-output-to-html-ts
  return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(text) }} />;
}

export async function PlainSummary({ q }: { q: string }) {
  const result = await generateText({ model: openai("gpt-4.1"), prompt: q });
  // ok: llm-output-to-html-ts
  return <div className="summary">{result.text}</div>;
}

export async function StepsSummary({ q }: { q: string }) {
  const result = await generateText({ model: openai("gpt-4.1"), prompt: q });
  // ruleid: llm-output-to-html-ts
  const markup = { __html: marked.parse(result.steps[0].text) as string };
  return <section dangerouslySetInnerHTML={markup} />;
}

export async function UsageBadge({ q }: { q: string }) {
  const result = await generateText({ model: openai("gpt-4.1"), prompt: q });
  // ok: llm-output-to-html-ts
  return <span dangerouslySetInnerHTML={{ __html: `<b>${result.usage.totalTokens}</b> tokens` }} />;
}

async function streamInto(el: HTMLElement, prompt: string) {
  const result = streamText({ model: openai("gpt-4.1"), prompt });
  let html = "";
  for await (const delta of result.textStream) {
    html += delta;
    // ruleid: llm-output-to-html-ts
    el.innerHTML = html;
  }
}

async function streamAsText(el: HTMLElement, prompt: string) {
  const result = streamText({ model: openai("gpt-4.1"), prompt });
  for await (const delta of result.textStream) {
    // ok: llm-output-to-html-ts
    el.textContent += delta;
  }
}

const triageAgent = new ToolLoopAgent({ model: openai("gpt-4.1"), instructions: "Triage tickets." });

async function triage(el: HTMLElement, ticket: string) {
  const result = await triageAgent.generate({ prompt: ticket });
  // ruleid: llm-output-to-html-ts
  el.insertAdjacentHTML("beforeend", result.text);
}

// --- AI SDK UI hooks (client components) ---

export function ChatLog() {
  const { messages } = useChat();
  return (
    <ol>
      {messages.map((message) => (
        <li key={message.id}>
          {message.parts.map((part, i) =>
            part.type === "text" ? (
              // ruleid: llm-output-to-html-ts
              <div key={i} dangerouslySetInnerHTML={{ __html: part.text }} />
            ) : null,
          )}
        </li>
      ))}
    </ol>
  );
}

export function SafeChatLog() {
  const { messages } = useChat();
  return (
    <ol>
      {messages.map((message) => (
        <li key={message.id}>
          {message.parts.map((part, i) =>
            // ok: llm-output-to-html-ts
            part.type === "text" ? <p key={i}>{part.text}</p> : null,
          )}
        </li>
      ))}
    </ol>
  );
}

export function Draft() {
  const { completion } = useCompletion({ api: "/api/draft" });
  // ruleid: llm-output-to-html-ts
  return <article dangerouslySetInnerHTML={{ __html: marked.parse(completion) as string }} />;
}

export function SafeDraft() {
  const { completion } = useCompletion({ api: "/api/draft" });
  const html = DOMPurify.sanitize(marked.parse(completion) as string);
  // ok: llm-output-to-html-ts
  return <article dangerouslySetInnerHTML={{ __html: html }} />;
}

export function MemoDraft() {
  const { completion } = useCompletion({ api: "/api/draft" });
  const html = useMemo(() => marked.parse(completion) as string, [completion]);
  // ruleid: llm-output-to-html-ts
  return <article dangerouslySetInnerHTML={{ __html: html }} />;
}

export function SafeMemoDraft() {
  const { completion } = useCompletion({ api: "/api/draft" });
  const html = useMemo(() => {
    const raw = marked.parse(completion) as string;
    return DOMPurify.sanitize(raw);
  }, [completion]);
  // ok: llm-output-to-html-ts
  return <article dangerouslySetInnerHTML={{ __html: html }} />;
}

export function MemoDraftWhenReady({ ready }: { ready: boolean }) {
  const { completion } = useCompletion({ api: "/api/draft" });
  const html = useMemo(() => (ready ? (marked.parse(completion) as string) : ""), [ready, completion]);
  // ruleid: llm-output-to-html-ts
  return <article dangerouslySetInnerHTML={{ __html: html }} />;
}

export function MemoDraftOrPlaceholder({ ready }: { ready: boolean }) {
  const { completion } = useCompletion({ api: "/api/draft" });
  const html = useMemo(() => {
    const placeholder = "<p>Drafting…</p>";
    return ready ? (marked.parse(completion) as string) : placeholder;
  }, [ready, completion]);
  // ruleid: llm-output-to-html-ts
  return <article dangerouslySetInnerHTML={{ __html: html }} />;
}

export function MemoDraftIfAny() {
  const { completion } = useCompletion({ api: "/api/draft" });
  const html = useMemo(() => completion && (marked.parse(completion) as string), [completion]);
  // ruleid: llm-output-to-html-ts
  return <article dangerouslySetInnerHTML={{ __html: html || "" }} />;
}

export function SafeMemoDraftWhenReady({ ready }: { ready: boolean }) {
  const { completion } = useCompletion({ api: "/api/draft" });
  const html = useMemo(
    () => (ready ? DOMPurify.sanitize(marked.parse(completion) as string) : ""),
    [ready, completion],
  );
  // ok: llm-output-to-html-ts
  return <article dangerouslySetInnerHTML={{ __html: html }} />;
}

// AI SDK 4 messages carried their text in `content`.
export function LegacyChatLog() {
  const { messages } = useChat();
  return messages.map((m) => (
    // ruleid: llm-output-to-html-ts
    <div key={m.id} className={m.role} dangerouslySetInnerHTML={{ __html: m.content }} />
  ));
}

export function ArticleCard({ schema }: { schema: any }) {
  const { object } = useObject({ api: "/api/article", schema });
  // ruleid: llm-output-to-html-ts
  return <div dangerouslySetInnerHTML={{ __html: object?.body ?? "" }} />;
}

// A message component typed with the AI SDK's UIMessage: the parent passes model output in.
export function Bubble({ message, compact }: { message: UIMessage; compact?: boolean }) {
  const text = message.parts.map((p) => (p.type === "text" ? p.text : "")).join("");
  // ruleid: llm-output-to-html-ts
  return <div className={compact ? "bubble small" : "bubble"} dangerouslySetInnerHTML={{ __html: text }} />;
}

interface PartProps {
  part: TextUIPart;
}

export function Part({ part }: PartProps) {
  // ruleid: llm-output-to-html-ts
  return <span dangerouslySetInnerHTML={{ __html: part.text }} />;
}

export function Title({ title }: { title: string }) {
  // ok: llm-output-to-html-ts
  return <h1 dangerouslySetInnerHTML={{ __html: title }} />;
}

// --- Markdown rendering ---

export function RawMarkdown() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown rehypePlugins={[rehypeRaw]}>
      {/* ruleid: llm-output-to-html-ts */}
      {completion}
    </ReactMarkdown>
  );
}

export function RawMarkdownChildrenProp() {
  const { completion } = useCompletion();
  // ruleid: llm-output-to-html-ts
  return <ReactMarkdown rehypePlugins={[[rehypeRaw, { passThrough: [] }]]} children={completion} />;
}

const rawPlugins = [rehypeRaw];

export function RawMarkdownPluginList() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown rehypePlugins={rawPlugins}>
      {/* ruleid: llm-output-to-html-ts */}
      {completion}
    </ReactMarkdown>
  );
}

export function SkipHtmlMarkdown() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown skipHtml rehypePlugins={[rehypeRaw]}>
      {/* ok: llm-output-to-html-ts */}
      {completion}
    </ReactMarkdown>
  );
}

const sanitizedPlugins = [rehypeRaw, rehypeSanitize];

export function SanitizedMarkdown() {
  const { completion } = useCompletion();
  return (
    <ReactMarkdown rehypePlugins={sanitizedPlugins}>
      {/* ok: llm-output-to-html-ts */}
      {completion}
    </ReactMarkdown>
  );
}

export function PlainMarkdown() {
  const { completion } = useCompletion();
  // ok: llm-output-to-html-ts
  return <ReactMarkdown>{completion}</ReactMarkdown>;
}

const md = markdownit({ linkify: true });
const mdWithHtml = markdownit({ html: true, linkify: true });

async function renderAnswer(el: HTMLElement, question: string) {
  const res = await openaiClient.chat.completions.create({
    model: "gpt-4.1",
    messages: [{ role: "user", content: question }],
  });
  const answer = res.choices[0].message.content ?? "";
  // ok: llm-output-to-html-ts
  el.innerHTML = md.render(answer);
  // ruleid: llm-output-to-html-ts
  el.innerHTML = mdWithHtml.render(answer);
  // ok: llm-output-to-html-ts
  el.textContent = answer;
  // ok: llm-output-to-html-ts
  el.innerHTML = `<small>${res.usage?.total_tokens} tokens, ${res.model}</small>`;
}

// --- OpenAI, Anthropic, Google, LangChain ---

async function respond(el: HTMLElement, input: string) {
  const response = await openaiClient.responses.create({ model: "gpt-4.1", input });
  // ruleid: llm-output-to-html-ts
  el.outerHTML = `<div class="answer">${response.output_text}</div>`;
}

async function streamChat(el: HTMLElement, input: string) {
  const stream = await openaiClient.chat.completions.create({
    model: "gpt-4.1",
    messages: [{ role: "user", content: input }],
    stream: true,
  });
  for await (const chunk of stream) {
    // ruleid: llm-output-to-html-ts
    el.innerHTML += chunk.choices[0]?.delta?.content || "";
  }
}

async function claudeAnswer(el: HTMLElement, input: string) {
  const msg = await anthropic.messages.create({
    model: "claude-sonnet-4-5",
    max_tokens: 1024,
    messages: [{ role: "user", content: input }],
  });
  const block = msg.content[0];
  if (block.type === "text") {
    // ruleid: llm-output-to-html-ts
    el.innerHTML = block.text;
    // ok: llm-output-to-html-ts
    el.innerHTML = sanitizeHtml(block.text);
    // ruleid: llm-output-to-html-ts
    el.innerHTML = sanitizeHtml(block.text, { allowedTags: false, allowedAttributes: false });
  }
}

function claudeStream(el: HTMLElement, input: string) {
  anthropic.messages
    .stream({ model: "claude-sonnet-4-5", max_tokens: 1024, messages: [{ role: "user", content: input }] })
    .on("text", (_delta, snapshot) => {
      // ruleid: llm-output-to-html-ts
      el.innerHTML = snapshot;
    });
}

async function geminiAnswer(ai: any, el: HTMLElement, input: string) {
  const response = await ai.models.generateContent({ model: "gemini-2.5-flash", contents: input });
  // ruleid: llm-output-to-html-ts
  el.innerHTML = response.text;
}

async function geminiChat(ai: any, el: HTMLElement, input: string) {
  const chat = ai.chats.create({ model: "gemini-2.5-flash" });
  const reply = await chat.sendMessage({ message: input });
  // ruleid: llm-output-to-html-ts
  el.insertAdjacentHTML("beforeend", reply.text);
}

async function chainAnswer(qaChain: any, el: HTMLElement, question: string) {
  const answer = await qaChain.invoke({ question });
  // ruleid: llm-output-to-html-ts
  el.innerHTML = answer;
}

async function ipcAnswer(ipcRenderer: any, el: HTMLElement) {
  const html = await ipcRenderer.invoke("render-release-notes");
  // ok: llm-output-to-html-ts
  el.innerHTML = html;
}

// --- Generated-page previews ---

export async function Preview({ brief }: { brief: string }) {
  const { text: page } = await generateText({ model: openai("gpt-4.1"), prompt: brief });
  return (
    <>
      {/* ruleid: llm-output-to-html-ts */}
      <iframe title="preview" srcDoc={page} />
      {/* ok: llm-output-to-html-ts */}
      <iframe title="preview" sandbox="allow-scripts" srcDoc={page} />
      {/* ruleid: llm-output-to-html-ts */}
      <iframe title="preview" sandbox="allow-scripts allow-same-origin" srcDoc={page} />
    </>
  );
}
