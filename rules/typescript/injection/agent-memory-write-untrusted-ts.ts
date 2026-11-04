import { openai } from "@ai-sdk/openai";
import { getStore, type LangGraphRunnableConfig } from "@langchain/langgraph";
import { Letta } from "@letta-ai/letta-client";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { ZepClient } from "@getzep/zep-cloud";
import { generateText } from "ai";
import MemoryClient from "mem0ai";
import { prisma } from "./db";

const client = new MemoryClient({ apiKey: process.env.MEM0_API_KEY ?? "" });
const letta = new Letta({ baseURL: "http://letta.internal.invalid:8283" });
const zep = new ZepClient({ apiKey: process.env.ZEP_API_KEY });
const seen = new Set<string>();

// ---- mem0 -------------------------------------------------------------------------------------

export async function saveLink(url: string, userId: string) {
  const res = await fetch(url);
  const page = await res.text();
  // ruleid: agent-memory-write-untrusted-ts
  await client.add([{ role: "user", content: page }], { user_id: userId });
}

export async function digestPage(url: string, userId: string) {
  const page = await (await fetch(url)).text();
  const summary = await generateText({ model: openai("gpt-5"), prompt: `Summarize for later: ${page}` });
  // A model's summary of the page carries what the page told it to say.
  // ruleid: agent-memory-write-untrusted-ts
  await client.add([{ role: "assistant", content: summary.text }], { userId });
}

export async function refreshMemory(memoryId: string, url: string) {
  const body = await (await fetch(url)).text();
  // ruleid: agent-memory-write-untrusted-ts
  await client.update(memoryId, { text: body });
}

export async function chat(message: string, userId: string) {
  const answer = await generateText({ model: openai("gpt-5"), prompt: message });
  // The user's own message and the model's reply to it: mem0's normal use.
  // ok: agent-memory-write-untrusted-ts
  await client.add([{ role: "user", content: message }, { role: "assistant", content: answer.text }], { userId });
}

export async function rememberScreened(url: string, userId: string) {
  const page = await (await fetch(url)).text();
  const clean = sanitizeForMemory(page);
  // ok: agent-memory-write-untrusted-ts
  await client.add([{ role: "user", content: clean }], { userId });
}

export async function recall(url: string, userId: string) {
  const page = await (await fetch(url)).text();
  // Searching with the page doesn't store it, and a Set has add() too.
  // ok: agent-memory-write-untrusted-ts
  seen.add(page);
  // ok: agent-memory-write-untrusted-ts
  return client.search(page, { filters: { user_id: userId } });
}

export async function rememberLength(url: string, userId: string) {
  const page = await (await fetch(url)).text();
  // ok: agent-memory-write-untrusted-ts
  await client.add([{ role: "user", content: `Fetched ${page.length} characters` }], { userId });
}

// ---- LangGraph store ---------------------------------------------------------------------------

export async function saveToolResult(mcp: Client, config: LangGraphRunnableConfig, userId: string) {
  const result = await mcp.callTool({ name: "fetch_issue", arguments: { id: 42 } });
  // ruleid: agent-memory-write-untrusted-ts
  await config.store?.put(["issues", userId], "latest", { text: JSON.stringify(result.content) });
}

export async function rememberTicket(ticketId: number) {
  const ticket = await prisma.ticket.findUnique({ where: { id: ticketId } });
  const store = getStore();
  // ruleid: agent-memory-write-untrusted-ts
  await store?.put(["tickets"], String(ticketId), { summary: ticket?.body });
}

export async function cacheOffline(db: IDBDatabase, url: string) {
  const page = await (await fetch(url)).text();
  const objectStore = db.transaction("pages", "readwrite").objectStore("pages");
  // IndexedDB's put(value, key).
  // ok: agent-memory-write-untrusted-ts
  objectStore.put(page, url);
}

export async function rememberStatus(config: LangGraphRunnableConfig, ticketId: number) {
  const ticket = await prisma.ticket.findUnique({ where: { id: ticketId } });
  // ok: agent-memory-write-untrusted-ts
  await config.store?.put(["tickets"], String(ticketId), { status: ticket?.status });
}

// ---- Letta ---------------------------------------------------------------------------------------

export async function pinTicket(agentId: string, ticketId: number) {
  const ticket = await prisma.ticket.findUnique({ where: { id: ticketId } });
  await letta.agents.blocks.update("customer", {
    agent_id: agentId,
    // ruleid: agent-memory-write-untrusted-ts
    value: ticket?.body ?? "",
  });
}

export async function archivePage(agentId: string, url: string) {
  const page = await (await fetch(url)).text();
  // ruleid: agent-memory-write-untrusted-ts
  await letta.agents.passages.create(agentId, { text: page });
}

export async function newBlock(url: string) {
  const page = await (await fetch(url)).text();
  // ruleid: agent-memory-write-untrusted-ts
  return letta.blocks.create({ label: "vendor_notes", value: page });
}

// ---- Zep -----------------------------------------------------------------------------------------

export async function graphPage(userId: string, url: string) {
  const page = await (await fetch(url)).text();
  // ruleid: agent-memory-write-untrusted-ts
  await zep.graph.add({ userId, type: "text", data: page });
}

export async function graphEpisode(graphUuid: string, url: string) {
  const page = await (await fetch(url)).text();
  // ruleid: agent-memory-write-untrusted-ts
  await zep.graph.episode.add(graphUuid, { data: page, type: "text" });
}

export async function threadPage(threadId: string, url: string) {
  const page = await (await fetch(url)).text();
  // ruleid: agent-memory-write-untrusted-ts
  await zep.thread.addMessages(threadId, { messages: [{ role: "user", content: page }] });
}

export async function threadUserTurn(threadId: string, message: string) {
  // ok: agent-memory-write-untrusted-ts
  await zep.thread.addMessages(threadId, { messages: [{ role: "user", content: message }] });
}
