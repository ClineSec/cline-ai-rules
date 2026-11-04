// mem0's open-source client, and clients from the app's own modules (no LangGraph import here).
import { Memory } from "mem0ai/oss";
import { memory, notes, store } from "./clients";

const local = new Memory();

export async function savePage(url: string, userId: string, namespace: string[]) {
  const page = await (await fetch(url)).text();
  // ruleid: agent-memory-write-untrusted-ts
  await local.add(page, { userId });
  // ruleid: agent-memory-write-untrusted-ts
  await local.update("mem-1", page);
  // A client named like mem0's, with mem0's scope ids.
  // ruleid: agent-memory-write-untrusted-ts
  await memory.add([{ role: "user", content: page }], { agentId: "researcher" });
  // An array namespace is LangGraph's shape.
  // ruleid: agent-memory-write-untrusted-ts
  await store.put(["pages", userId], url, { text: page });
  // Another kind of store, without LangGraph in the file.
  // ok: agent-memory-write-untrusted-ts
  await store.put(namespace, url, { text: page });
  // No mem0 scope ids: some other add().
  // ok: agent-memory-write-untrusted-ts
  await memory.add(page);
  // ok: agent-memory-write-untrusted-ts
  await notes.add(page, { userId });
}
