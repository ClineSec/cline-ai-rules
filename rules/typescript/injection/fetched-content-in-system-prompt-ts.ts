import Anthropic from "@anthropic-ai/sdk";
import { openai } from "@ai-sdk/openai";
import { createStuffDocumentsChain } from "@langchain/classic/chains/combine_documents";
import { CheerioWebBaseLoader } from "@langchain/community/document_loaders/web/cheerio";
import { DuckDuckGoSearch } from "@langchain/community/tools/duckduckgo_search";
import { SerpAPI } from "@langchain/community/tools/serpapi";
import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { RunnablePassthrough, RunnableSequence } from "@langchain/core/runnables";
import type { VectorStore } from "@langchain/core/vectorstores";
import { ChatOpenAI } from "@langchain/openai";
import { Pinecone } from "@pinecone-database/pinecone";
import { PrismaClient } from "@prisma/client";
import { tavily } from "@tavily/core";
import { generateText, streamText, ToolLoopAgent } from "ai";
import axios from "axios";
import * as cheerio from "cheerio";
import { ChromaClient } from "chromadb";
import { eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/node-postgres";
import Exa from "exa-js";
import express from "express";
import { google } from "googleapis";
import { chromium } from "playwright";
import { createAgent, dynamicSystemPromptMiddleware } from "langchain";
import OpenAI from "openai";
import { Pool } from "pg";
import puppeteer from "puppeteer";
import { getJson } from "serpapi";
import * as DDG from "duck-duck-scrape";
import Firecrawl from "@mendable/firecrawl-js";
import { Agent, run, tool } from "@openai/agents";
import { RealtimeAgent } from "@openai/agents/realtime";
import { z } from "zod";
import { comments } from "./schema";

const anthropic = new Anthropic();
const client = new OpenAI();
const llm = new ChatOpenAI({ model: "gpt-5" });
const prisma = new PrismaClient();
const pool = new Pool();
const db = drizzle(pool);
const app = express();
declare const vectorStore: VectorStore;

// ---- Retrieved documents ---------------------------------------------------------------------

export async function POST(req: Request) {
  const { question } = await req.json();
  const docs = await vectorStore.asRetriever({ k: 4 }).invoke(question);
  const context = docs.map((d) => d.pageContent).join("\n\n");
  const result = streamText({
    model: openai("gpt-5"),
    // ruleid: fetched-content-in-system-prompt-ts
    system: `Answer from these articles only:\n${context}`,
    // ok: fetched-content-in-system-prompt-ts
    prompt: question,
  });
  return result.toUIMessageStreamResponse();
}

export async function PUT(req: Request) {
  const { question } = await req.json();
  const hits = await vectorStore.similaritySearch(question, 3);
  return client.chat.completions.create({
    model: "gpt-5",
    messages: [
      // ruleid: fetched-content-in-system-prompt-ts
      { role: "developer", content: "Use this context: " + hits[0].pageContent },
      { role: "user", content: question },
    ],
  });
}

export async function PATCH(req: Request) {
  const { question } = await req.json();
  const docs = await vectorStore.similaritySearch(question, 3);
  const articles = docs.map((d) => d.pageContent).join("\n\n");
  const { text } = await generateText({
    model: openai("gpt-5"),
    // ok: fetched-content-in-system-prompt-ts
    instructions: `Answer from the articles in the user turn. ${docs.length} articles were found.`,
    // ok: fetched-content-in-system-prompt-ts
    prompt: `<articles>\n${articles}\n</articles>\n\n${question}`,
  });
  return Response.json({ text });
}

async function findRelevantContent(query: string) {
  return [{ name: "kb-1", content: query }];
}

export async function GET(req: Request) {
  const question = new URL(req.url).searchParams.get("q") ?? "";
  const relevant = await findRelevantContent(question);
  const agent = new ToolLoopAgent({
    model: openai("gpt-5"),
    // ruleid: fetched-content-in-system-prompt-ts
    instructions: `Ground your answer in: ${JSON.stringify(relevant)}`,
  });
  return Response.json(await agent.generate({ prompt: question }));
}

// ---- Loaders and fetched pages ---------------------------------------------------------------

export async function summarizePage(url: string) {
  const loader = new CheerioWebBaseLoader(url);
  const pages = await loader.load();
  return llm.invoke([
    // ruleid: fetched-content-in-system-prompt-ts
    new SystemMessage(`Summarize this page for the user:\n${pages[0].pageContent}`),
    new HumanMessage("Summarize it."),
  ]);
}

export async function describeLink(pageUrl: string) {
  const res = await fetch(pageUrl);
  const html = await res.text();
  const text = cheerio.load(html)("main").text();
  return anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 512,
    // ruleid: fetched-content-in-system-prompt-ts
    system: "You describe web pages. Page text:\n" + text.slice(0, 8000),
    messages: [{ role: "user", content: "Describe it." }],
  });
}

export async function describeLinkAxios(link: string) {
  const { data: html } = await axios.get(link, { responseType: "text" });
  return client.responses.create({
    model: "gpt-5",
    // ruleid: fetched-content-in-system-prompt-ts
    instructions: `Page:\n${html}`,
    input: "Summarize.",
  });
}

export async function readRenderedPage(target: string) {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(target);
  const visible = await page.innerText("main");
  await browser.close();
  // ruleid: fetched-content-in-system-prompt-ts
  return new ToolLoopAgent({ model: openai("gpt-5"), instructions: `Rendered page:\n${visible}` });
}

export async function pageTitleOnly(target: string) {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(target);
  const status = page.url();
  await browser.close();
  // ok: fetched-content-in-system-prompt-ts
  return new ToolLoopAgent({ model: openai("gpt-5"), instructions: `The browser is on ${status}.` });
}

export async function statusBanner(statusUrl: string) {
  const status = await (await fetch(statusUrl)).json();
  return anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 256,
    // ok: fetched-content-in-system-prompt-ts
    system: `Service status: ${status.state}. Open incidents: ${status.openCount}.`,
    messages: [{ role: "user", content: "Any outages?" }],
  });
}

export async function incidentBrief(statusUrl: string) {
  const { data } = await axios.get(statusUrl);
  return anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 256,
    // ruleid: fetched-content-in-system-prompt-ts
    system: "Current incident: " + data.incident.description,
    messages: [{ role: "user", content: "What is happening?" }],
  });
}

export async function runbookFromTool(mcp: { callTool: (r: object) => Promise<any> }, service: string) {
  // An MCP server's tool result: the server's operator wrote it.
  const result = await mcp.callTool({ name: "get_runbook", arguments: { service } });
  return anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 512,
    // ruleid: fetched-content-in-system-prompt-ts
    system: `Follow this runbook:\n${result.content[0].text}`,
    messages: [{ role: "user", content: "The service is down." }],
  });
}

// ---- Stored records --------------------------------------------------------------------------

app.post("/tickets/:id/draft", async (req, res) => {
  const ticket = await prisma.ticket.findUnique({ where: { id: Number(req.params.id) } });
  const reply = await anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 1024,
    // ruleid: fetched-content-in-system-prompt-ts
    system: `Ticket #${ticket?.id} (${ticket?.status}): ${ticket?.body}`,
    messages: [{ role: "user", content: "Draft a reply." }],
  });
  res.json(reply);
});

app.post("/tickets/:id/status", async (req, res) => {
  const ticket = await prisma.ticket.findUnique({ where: { id: Number(req.params.id) } });
  const reply = await anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 256,
    // ok: fetched-content-in-system-prompt-ts
    system: `Ticket #${ticket?.id} is ${ticket?.status}, priority ${ticket?.priority}.`,
    messages: [{ role: "user", content: ticket?.body ?? "" }],
  });
  res.json(reply);
});

app.post("/tickets/:id/thread", async (req, res) => {
  const rows = await db.select().from(comments).where(eq(comments.ticketId, Number(req.params.id)));
  const history = rows.map((c) => `- ${c.author}: ${c.text}`).join("\n");
  const { text } = await generateText({
    model: openai("gpt-5"),
    // ruleid: fetched-content-in-system-prompt-ts
    system: "Thread so far:\n" + history,
    prompt: "Summarize the thread.",
  });
  res.json({ text });
});

app.post("/tickets/:id/pg", async (req, res) => {
  const { rows } = await pool.query("SELECT body FROM tickets WHERE id = $1", [req.params.id]);
  const agent = new ToolLoopAgent({
    model: openai("gpt-5"),
    // ruleid: fetched-content-in-system-prompt-ts
    instructions: "Reply to this ticket:\n" + rows[0].body,
  });
  res.json(await agent.generate({ prompt: "Draft a reply." }));
});

app.post("/tenants/:id/chat", async (req, res) => {
  const settings = await prisma.tenantSettings.findFirst({ where: { tenantId: req.params.id } });
  const reply = await anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 512,
    // ok: fetched-content-in-system-prompt-ts
    system: `${settings?.personaText}\n${settings?.description}`,
    messages: [{ role: "user", content: String(req.body.question) }],
  });
  res.json(reply);
});

async function getTicket(id: string) {
  return { id, lastMessage: "", status: "open" };
}

async function getTenantPersona(id: string) {
  return { text: `persona for ${id}` };
}

app.post("/tickets/:id/helper", async (req, res) => {
  const ticket = await getTicket(req.params.id);
  const persona = await getTenantPersona(String(req.query.tenant));
  const reply = await anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 512,
    // ruleid: fetched-content-in-system-prompt-ts
    system: `${persona.text}\n\nThe customer's last message: ${ticket.lastMessage}`,
    messages: [{ role: "user", content: "Draft a reply." }],
  });
  res.json(reply);
});

app.post("/tenants/:id/persona", async (req, res) => {
  const persona = await getTenantPersona(req.params.id);
  const reply = await anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 512,
    // ok: fetched-content-in-system-prompt-ts
    system: persona.text,
    messages: [{ role: "user", content: String(req.body.question) }],
  });
  res.json(reply);
});

// ---- LangChain.js templates, chains, and middleware ------------------------------------------

const RAG_SYSTEM = "Answer using only this context:\n{context}";
const ragPrompt = ChatPromptTemplate.fromMessages([
  ["system", RAG_SYSTEM],
  ["human", "{question}"],
]);
const ragChain = ragPrompt.pipe(llm).pipe(new StringOutputParser());
const userTurnPrompt = ChatPromptTemplate.fromMessages([
  ["system", "Answer from the context in the user message."],
  ["human", "Context:\n{context}\n\n{question}"],
]);

const formatDocs = (docs: { pageContent: string }[]) => docs.map((d) => d.pageContent).join("\n\n");

export async function ragAnswer(question: string) {
  const docs = await vectorStore.similaritySearch(question);
  return ragChain.invoke({
    // ruleid: fetched-content-in-system-prompt-ts
    context: formatDocs(docs),
    // ok: fetched-content-in-system-prompt-ts
    question,
  });
}

export async function ragAnswerUserTurn(question: string) {
  const docs = await vectorStore.similaritySearch(question);
  // ok: fetched-content-in-system-prompt-ts
  return userTurnPrompt.pipe(llm).invoke({ context: formatDocs(docs), question });
}

const docsRetriever = vectorStore.asRetriever();
const lcelPrompt = ChatPromptTemplate.fromMessages([
  ["system", "You are the docs assistant. Context:\n{context}"],
  ["human", "{question}"],
]);
export const lcelChain = RunnableSequence.from([
  // ruleid: fetched-content-in-system-prompt-ts
  { context: docsRetriever.pipe(formatDocs), question: new RunnablePassthrough() },
  lcelPrompt,
  llm,
]);

const stuffPrompt = ChatPromptTemplate.fromMessages([
  // ruleid: fetched-content-in-system-prompt-ts
  ["system", "Use the following documents to answer.\n\n{context}"],
  ["human", "{input}"],
]);
export const combineChain = await createStuffDocumentsChain({ llm, prompt: stuffPrompt });

const stuffUserPrompt = ChatPromptTemplate.fromMessages([
  // ok: fetched-content-in-system-prompt-ts
  ["system", "Answer from the documents in the user message."],
  ["human", "Documents:\n{context}\n\n{input}"],
]);
export const combineUserChain = await createStuffDocumentsChain({ llm, prompt: stuffUserPrompt });

export const ragAgent = createAgent({
  model: "openai:gpt-5",
  middleware: [
    dynamicSystemPromptMiddleware(async (state) => {
      const lastQuery = String(state.messages.at(-1)?.content ?? "");
      const retrieved = await vectorStore.similaritySearch(lastQuery);
      const docsContent = retrieved.map((doc) => doc.pageContent).join("\n\n");
      // ruleid: fetched-content-in-system-prompt-ts
      return `You are a helpful assistant. Use the following context in your response:\n\n${docsContent}`;
    }),
  ],
});

app.get("/threads/:id/header", async (req, res) => {
  const thread = await prisma.ticketThread.findUnique({ where: { id: req.params.id } });
  const reply = await anthropic.messages.create({
    model: "claude-sonnet-5-5",
    max_tokens: 128,
    // ok: fetched-content-in-system-prompt-ts
    system: `The thread is ${thread?.status} with ${thread?.messages.length} messages.`,
    messages: [{ role: "user", content: "Write a header." }],
  });
  res.json(reply);
});

const tvly = tavily({ apiKey: "tvly-fake-key-for-tests" });
const exa = new Exa("fake-exa-key-for-tests");
const firecrawl = new Firecrawl({ apiKey: "fc-fake-key-for-tests" });
const chroma = new ChromaClient();
const pinecone = new Pinecone({ apiKey: "fake-pinecone-key" });

app.get("/research", async (req, res) => {
  const found = await tvly.search(String(req.query.topic), { maxResults: 3 });
  const sources = found.results.map((r) => r.content).join("\n");
  // ruleid: fetched-content-in-system-prompt-ts
  const { text } = await generateText({ model: openai("gpt-5"), system: `Sources:\n${sources}`, prompt: "Brief?" });
  res.json({ text });
});

app.get("/exa", async (req, res) => {
  const results = await exa.searchAndContents(String(req.query.topic), { text: true, numResults: 3 });
  // ruleid: fetched-content-in-system-prompt-ts
  const { text } = await generateText({ model: openai("gpt-5"), system: `Sources:\n${results.results.map((r) => r.text).join("\n")}`, prompt: "Brief?" });
  res.json({ text });
});

app.get("/scrape", async (req, res) => {
  const doc = await firecrawl.scrape(String(req.query.url), { formats: ["markdown"] });
  // ruleid: fetched-content-in-system-prompt-ts
  const { text } = await generateText({ model: openai("gpt-5"), instructions: `Summarize:\n${doc.markdown}`, prompt: "Summary?" });
  res.json({ text });
});

app.get("/chroma", async (req, res) => {
  const collection = await chroma.getCollection({ name: "handbook" });
  const found = await collection.query({ queryTexts: [String(req.query.q)], nResults: 4 });
  const context = found.documents[0].join("\n\n");
  // ruleid: fetched-content-in-system-prompt-ts
  const { text } = await generateText({ model: openai("gpt-5"), system: `Context:\n${context}`, prompt: String(req.query.q) });
  res.json({ text });
});

app.post("/pinecone", async (req, res) => {
  const index = pinecone.index("handbook");
  const found = await index.query({ vector: req.body.vector, topK: 4, includeMetadata: true });
  const context = found.matches.map((m) => m.metadata?.text).join("\n\n");
  // ruleid: fetched-content-in-system-prompt-ts
  const { text } = await generateText({ model: openai("gpt-5"), system: `Context:\n${context}`, prompt: req.body.q });
  res.json({ text });
});

app.post("/weaviate", async (req, res) => {
  const response = await req.app.locals.articles.query.nearText(req.body.q, { limit: 3 });
  const context = response.objects.map((o) => o.properties.body).join("\n\n");
  // ruleid: fetched-content-in-system-prompt-ts
  const { text } = await generateText({ model: openai("gpt-5"), system: `Articles:\n${context}`, prompt: req.body.q });
  res.json({ text });
});

app.post("/style", async (req, res) => {
  const shots = await req.app.locals.examples.search(req.body.q);
  // ok: fetched-content-in-system-prompt-ts
  const { text } = await generateText({ model: openai("gpt-5"), system: `Answer like these examples: ${shots}`, prompt: req.body.q });
  res.json({ text });
});

class HandbookBot {
  constructor(private retriever: { invoke(q: string): Promise<{ pageContent: string }[]> }) {}

  async answer(question: string) {
    const docs = await this.retriever.invoke(question);
    // ruleid: fetched-content-in-system-prompt-ts
    const { text } = await generateText({ model: openai("gpt-5"), system: `Answer from:\n${docs.map((d) => d.pageContent).join("\n")}`, prompt: question });
    return text;
  }
}

app.get("/web/lc", async (req, res) => {
  const topic = String(req.query.topic);
  const serp = await new SerpAPI("fake-serpapi-key").invoke(topic);
  const ddg = await new DuckDuckGoSearch({ maxResults: 3 }).invoke(topic);
  // ruleid: fetched-content-in-system-prompt-ts
  const { text } = await generateText({ model: openai("gpt-5"), system: `SerpAPI: ${serp}\nDuckDuckGo: ${ddg}`, prompt: topic });
  res.json({ text });
});

app.get("/web/serpapi", async (req, res) => {
  const found = await getJson({ engine: "google", q: String(req.query.topic), api_key: "fake-serpapi-key" });
  const snippets = found.organic_results.map((r: { snippet: string }) => r.snippet).join("\n");
  // ruleid: fetched-content-in-system-prompt-ts
  const { text } = await generateText({ model: openai("gpt-5"), system: `Background:\n${snippets}`, prompt: "Brief?" });
  res.json({ text });
});

app.get("/web/ddg", async (req, res) => {
  const found = await DDG.search(String(req.query.topic));
  const lines = found.results.map((r) => `${r.title}: ${r.description}`).join("\n");
  // ruleid: fetched-content-in-system-prompt-ts
  const { text } = await generateText({ model: openai("gpt-5"), system: `Results:\n${lines}`, prompt: "Brief?" });
  res.json({ text });
});

app.get("/web/cse", async (req, res) => {
  const cse = google.customsearch("v1");
  const found = await cse.cse.list({ q: String(req.query.topic), cx: "fake-engine-id", key: "fake-google-key" });
  // ruleid: fetched-content-in-system-prompt-ts
  const { text } = await generateText({ model: openai("gpt-5"), system: `Results: ${JSON.stringify(found.data.items)}`, prompt: "Brief?" });
  res.json({ text });
});

app.get("/web/jina", async (req, res) => {
  const page = await fetch(`https://r.jina.ai/${String(req.query.url)}`);
  const markdown = await page.text();
  // ruleid: fetched-content-in-system-prompt-ts
  const { text } = await generateText({ model: openai("gpt-5"), system: `Summarize:\n${markdown.slice(0, 6000)}`, prompt: "Summary?" });
  res.json({ text });
});

app.get("/web/engine", async (req, res) => {
  const searchToolName = String(req.query.engine) === "bing" ? "Bing" : "DuckDuckGo";
  // ok: fetched-content-in-system-prompt-ts
  const { text } = await generateText({ model: openai("gpt-5"), system: `You search with ${searchToolName}.`, prompt: "Hi" });
  res.json({ text });
});

export async function readByScript(target: string) {
  const browser = await puppeteer.launch();
  const tab = await browser.newPage();
  await tab.goto(target);
  const all = await tab.evaluate(() => document.body.innerText);
  const lead = await tab.$eval("article p", (el) => el.textContent);
  const markup = await tab.content();
  const depth = await tab.evaluate(() => window.scrollY);
  await browser.close();
  return [
    // ruleid: fetched-content-in-system-prompt-ts
    new ToolLoopAgent({ model: openai("gpt-5"), instructions: `Page text:\n${all}` }),
    // ruleid: fetched-content-in-system-prompt-ts
    new ToolLoopAgent({ model: openai("gpt-5"), instructions: `Lead paragraph: ${lead}` }),
    // ruleid: fetched-content-in-system-prompt-ts
    new ToolLoopAgent({ model: openai("gpt-5"), instructions: `Markup:\n${markup}` }),
    // ok: fetched-content-in-system-prompt-ts
    new ToolLoopAgent({ model: openai("gpt-5"), instructions: `The reader scrolled ${depth} pixels.` }),
  ];
}


// OpenAI Agents SDK (@openai/agents-core 0.21.0): what a tool's execute() returns becomes a tool
// result, which the model reads as data. Only instructions (a string, or what the instructions
// function returns) is the system prompt.
const BULLETIN_URL = "https://service.example.com/bulletins.json";

export const warrantyDesk = new RealtimeAgent({
  name: "warranty",
  instructions: "You help riders file warranty claims for e-bike batteries.",
  tools: [
    tool({
      name: "assessClaim",
      description: "Ask the claims model whether a battery claim qualifies.",
      parameters: z.object({ serial: z.string(), symptom: z.string() }),
      execute: async (input) => {
        const resp = await fetch("/api/responses", {
          method: "POST",
          body: JSON.stringify({ model: "o4-mini", input: `${input.serial}: ${input.symptom}` }),
        });
        if (!resp.ok) {
          return { error: "The claims service is unavailable." };
        }
        const { output = [] } = await resp.json();
        const verdict = output
          // ok: fetched-content-in-system-prompt-ts
          .find((o: any) => o.type === "message" && o.role === "assistant")
          // ok: fetched-content-in-system-prompt-ts
          ?.content?.find((c: any) => c.type === "output_text")?.text ?? "";
        // ok: fetched-content-in-system-prompt-ts
        return { result: verdict || output };
      },
    }),
    tool({
      name: "claimHistory",
      description: "Summarize the earlier claims on a battery.",
      parameters: z.object({ serial: z.string() }),
      execute: async ({ serial }) => {
        const page = await fetch(`https://claims.example.com/history/${serial}`);
        const history = await page.text();
        const summary = await client.chat.completions.create({
          model: "gpt-5",
          messages: [
            // ruleid: fetched-content-in-system-prompt-ts
            { role: "system", content: `Summarize this claim history:\n${history}` },
            { role: "user", content: serial },
          ],
        });
        // ok: fetched-content-in-system-prompt-ts
        return { result: summary.choices[0].message.content };
      },
    }),
  ],
});

export const bulletinDesk = new Agent({
  name: "bulletins",
  instructions: async (runContext) => {
    const resp = await fetch(BULLETIN_URL);
    const bulletins = await resp.text();
    // ruleid: fetched-content-in-system-prompt-ts
    return `Apply these service bulletins:\n${bulletins}`;
  },
  tools: [
    tool({
      name: "partsList",
      description: "List the parts for a model.",
      parameters: z.object({ model: z.string() }),
      execute: async ({ model }) => {
        const resp = await fetch(`https://parts.example.com/${model}`);
        const body = await resp.text();
        // ok: fetched-content-in-system-prompt-ts
        return body;
      },
    }),
  ],
});

async function recallBrief(runContext: unknown): Promise<string> {
  const resp = await fetch("https://service.example.com/recalls.json");
  const recalls: { title: string; body: string }[] = await resp.json();
  // ok: fetched-content-in-system-prompt-ts
  const headlines = recalls.map((r) => r.title);
  // ruleid: fetched-content-in-system-prompt-ts
  return `Open recalls: ${headlines.join("; ")}`;
}

export const recallDesk = new Agent({ name: "recalls", instructions: recallBrief });

export const fitDesk = new Agent({
  name: "fit",
  instructions: async (runContext) => {
    const resp = await fetch("https://service.example.com/fit-guide.json");
    const guide: { title: string; body: string }[] = await resp.json();
    if (guide.length === 0) {
      // ok: fetched-content-in-system-prompt-ts
      return "Size frames from the rider's inseam.";
    }
    if (guide.length === 1) {
      // ruleid: fetched-content-in-system-prompt-ts
      return `Fit guide: ${guide[0].body}`;
    }
    // ok: fetched-content-in-system-prompt-ts
    const sections = guide.filter((g) => g.title).map((g) => g.title);
    // ruleid: fetched-content-in-system-prompt-ts
    return `Fit guide sections: ${sections.join(", ")}`;
  },
});

const tuneUpNotes = async (runContext: unknown): Promise<string> => {
  const resp = await fetch("https://service.example.com/tune-up.md");
  if (!resp.ok) {
    // ok: fetched-content-in-system-prompt-ts
    return "Walk the rider through a basic tune-up.";
  }
  const markdown = await resp.text();
  // ruleid: fetched-content-in-system-prompt-ts
  return `Tune-up checklist:\n${markdown}`;
};

// ruleid: fetched-content-in-system-prompt-ts
const quickNotes = async () => (await (await fetch("https://service.example.com/quick.md")).text());

export const tuneUpDesk = new Agent({ name: "tune-up", instructions: tuneUpNotes });
export const quickDesk = new Agent({ name: "quick", instructions: quickNotes });

const unusedNotes = async () => {
  const resp = await fetch("https://service.example.com/drafts.md");
  const draft = await resp.text();
  // ok: fetched-content-in-system-prompt-ts
  return draft;
};

// Agents built per request inside a route handler: the instructions function's early returns
// count; what its callbacks and the agent's tools return does not.
app.post("/shops/:shop/fit", async (req, res) => {
  const shopFit = new Agent({
    name: "shop-fit",
    instructions: async () => {
      const resp = await fetch(`https://shops.example.com/${req.params.shop}/fit-notes.md`);
      if (resp.ok) {
        // ruleid: fetched-content-in-system-prompt-ts
        return `Shop fit notes:\n${await resp.text()}`;
      }
      // ok: fetched-content-in-system-prompt-ts
      return "Size frames from the rider's inseam.";
    },
    tools: [
      tool({
        name: "stock",
        description: "Check frame stock at the shop.",
        parameters: z.object({ size: z.string() }),
        execute: async ({ size }) => {
          const page = await fetch(`https://shops.example.com/${req.params.shop}/stock/${size}`);
          // ok: fetched-content-in-system-prompt-ts
          return { result: await page.text() };
        },
      }),
    ],
  });
  res.json((await run(shopFit, req.body.question)).finalOutput);
});

app.post("/shops/:shop/service", async (req, res) => {
  const serviceNotes = async () => {
    const resp = await fetch(`https://shops.example.com/${req.params.shop}/service.json`);
    const notes: { title: string; body: string }[] = await resp.json();
    for (const note of notes) {
      if (note.title === "pinned") {
        // ruleid: fetched-content-in-system-prompt-ts
        return `Pinned service note: ${note.body}`;
      }
    }
    // ok: fetched-content-in-system-prompt-ts
    const titles = notes.map((n) => n.title);
    // ruleid: fetched-content-in-system-prompt-ts
    return `Service topics: ${titles.join(", ")}`;
  };
  const serviceDesk = new Agent({ name: "service", instructions: serviceNotes });
  res.json((await run(serviceDesk, req.body.question)).finalOutput);
});

async function stormNotice(runContext: unknown): Promise<string> {
  const resp = await fetch("https://service.example.com/storm.json");
  const notice: { active: boolean; text: string } = await resp.json();
  if (notice.active) {
    // ruleid: fetched-content-in-system-prompt-ts
    return `Storm notice: ${notice.text}`;
  }
  // ok: fetched-content-in-system-prompt-ts
  return "No weather notices today.";
}

export const stormDesk = new Agent({ name: "storm", instructions: stormNotice });
