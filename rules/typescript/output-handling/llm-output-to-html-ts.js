// A plain-DOM help widget (no framework), with a LangChain.js backend helper in the same bundle.
import { ChatOpenAI } from "@langchain/openai";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import DOMPurify from "dompurify";
import { Marked } from "marked";
import showdown from "showdown";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import rehypeSanitize from "rehype-sanitize";
import rehypeStringify from "rehype-stringify";

const model = new ChatOpenAI({ model: "gpt-4.1" });
const prompt = ChatPromptTemplate.fromTemplate("Answer briefly: {question}");
const chain = prompt.pipe(model).pipe(new StringOutputParser());
const converter = new showdown.Converter();

export async function answerInto(panel, question) {
  const answer = await chain.invoke({ question });
  // ruleid: llm-output-to-html-ts
  panel.innerHTML = converter.makeHtml(answer);
  // ok: llm-output-to-html-ts
  panel.innerHTML = DOMPurify.sanitize(converter.makeHtml(answer));
}

export async function streamInto(panel, question) {
  const stream = await chain.stream({ question });
  let text = "";
  for await (const chunk of stream) {
    text += chunk;
    // ruleid: llm-output-to-html-ts
    panel.replaceChildren(document.createRange().createContextualFragment(text));
  }
}

export async function printable(question) {
  const reply = await model.invoke(question);
  const win = window.open("", "_blank");
  // ruleid: llm-output-to-html-ts
  win.document.write(`<pre>${reply.content}</pre>`);
}

export async function preview(frame, question) {
  const reply = await model.invoke(question);
  // ruleid: llm-output-to-html-ts
  frame.srcdoc = reply.content;
}

export async function sandboxedPreview(frame, question) {
  const reply = await model.invoke(question);
  frame.setAttribute("sandbox", "allow-scripts");
  // ok: llm-output-to-html-ts
  frame.srcdoc = reply.content;
}

export async function unsafeHtml(el, question) {
  const reply = await model.invoke(question);
  // ruleid: llm-output-to-html-ts
  el.setHTMLUnsafe(reply.content);
}

const safeMarked = new Marked({ hooks: { postprocess: (html) => DOMPurify.sanitize(html) } });
const plainMarked = new Marked();

export async function markedAnswer(el, question) {
  const reply = await model.invoke(question);
  // ok: llm-output-to-html-ts
  el.innerHTML = safeMarked.parse(reply.content);
  // ruleid: llm-output-to-html-ts
  el.innerHTML = plainMarked.parse(reply.content);
}

const sanitizingPipeline = unified().use(remarkParse).use(remarkRehype).use(rehypeSanitize).use(rehypeStringify);

export async function unifiedAnswer(el, question) {
  const reply = await model.invoke(question);
  // ok: llm-output-to-html-ts
  el.innerHTML = String(await sanitizingPipeline.process(reply.content));
}

// jQuery embeds.
export async function jqueryAnswer(question) {
  const reply = await model.invoke(question);
  // ruleid: llm-output-to-html-ts
  $("#hw-answer").html(reply.content);
  // ok: llm-output-to-html-ts
  $("#hw-answer").text(reply.content);
  // ruleid: llm-output-to-html-ts
  $("#hw-log").append(`<div class="hw-bubble">${reply.content}</div>`);
  // ruleid: llm-output-to-html-ts
  jQuery(".hw-log").find("li").last().after(reply.content);
  const $card = $("<div class='hw-card'></div>");
  // ruleid: llm-output-to-html-ts
  $card.prepend(reply.content);
  // ruleid: llm-output-to-html-ts
  $(reply.content).appendTo("#hw-log");
  // ok: llm-output-to-html-ts
  $("#hw-log").append($("<div class='hw-bubble'></div>").text(reply.content));
  const bubble = document.createElement("div");
  // ok: llm-output-to-html-ts
  bubble.append(reply.content);
}
