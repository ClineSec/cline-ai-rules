import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import Anthropic from "@anthropic-ai/sdk";
import Handlebars from "handlebars";
import _ from "lodash";
import template from "lodash/template";
import * as ejs from "ejs";
import nunjucks, { Environment, Template } from "nunjucks";
import pug from "pug";
import { Eta } from "eta";
import Mustache from "mustache";
import { PromptTemplate } from "@langchain/core/prompts";

const anthropic = new Anthropic();
const eta = new Eta({ views: "./templates" });
const env = new Environment();

const REPLY_LAYOUT = "<p>Hi {{name}},</p><div>{{reply}}</div>";

export async function handlebarsMacro(name: string) {
  const { text } = await generateText({ model: openai("gpt-5"), prompt: "Write the macro" });
  // ruleid: llm-output-as-template-ts
  const render = Handlebars.compile(text);
  // ok: llm-output-as-template-ts
  const layout = Handlebars.compile(REPLY_LAYOUT);
  return [render({ name }), layout({ name, reply: text })];
}

export async function lodashLayout() {
  const result = await generateText({ model: openai("gpt-5"), prompt: "Write the layout" });
  // ruleid: llm-output-as-template-ts
  const compiled = _.template(`<main>${result.text}</main>`);
  // ruleid: llm-output-as-template-ts
  const other = template(result.text);
  return compiled({ user: "ops" }) + other({});
}

export async function ejsAndPug() {
  const message = await anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 800,
    messages: [{ role: "user", content: "Write the page" }],
  });
  const body = message.content[0].type === "text" ? message.content[0].text : "";
  // ruleid: llm-output-as-template-ts
  const page = ejs.render(body, { user: "ops" });
  // ruleid: llm-output-as-template-ts
  const fn = pug.compile(body);
  // ok: llm-output-as-template-ts
  const fixed = ejs.render("<p><%= body %></p>", { body });
  return [page, fn({}), fixed];
}

export async function nunjucksTemplates() {
  const { text } = await generateText({ model: openai("gpt-5"), prompt: "Write the summary" });
  // ruleid: llm-output-as-template-ts
  const a = nunjucks.renderString(text, { user: "ops" });
  // ruleid: llm-output-as-template-ts
  const b = new Template(text);
  // ruleid: llm-output-as-template-ts
  const c = env.renderString("{% extends 'base.njk' %}" + text, {});
  // ok: llm-output-as-template-ts
  const d = env.render("summary.njk", { summary: text });
  const configured = nunjucks.configure("views", { autoescape: true });
  // ruleid: llm-output-as-template-ts
  const e = configured.renderString(text, {});
  return [a, b, c, d, e];
}

export async function etaTemplates() {
  const { text } = await generateText({ model: openai("gpt-5"), prompt: "Write the digest" });
  // ruleid: llm-output-as-template-ts
  const digest = eta.renderString(text, { user: "ops" });
  // ruleid: llm-output-as-template-ts
  const compiled = eta.compile(text);
  // ok: llm-output-as-template-ts
  const fixed = eta.render("./digest", { body: text });
  return [digest, compiled, fixed];
}

export async function logicLess() {
  const { text } = await generateText({ model: openai("gpt-5"), prompt: "Write the macro" });
  // ok: llm-output-as-template-ts
  const reply = Mustache.render(text, { name: "Ada" });
  // ok: llm-output-as-template-ts
  const prompt = PromptTemplate.fromTemplate(text, { templateFormat: "mustache" });
  // ok: llm-output-as-template-ts
  const count = _.template(String(Number(text)));
  return [reply, prompt, count];
}
