import { Letta } from "@letta-ai/letta-client";
import MemoryClient from "mem0ai";

// Long-term memory for the support assistant. mem0 keeps what each customer has told the chat
// (preferences, their setup, links they shared) across conversations; the Letta agent behind
// the agent-assist panel keeps a "known issues" core memory block that every draft sees.
export const customerMemory = new MemoryClient({ apiKey: process.env.MEM0_API_KEY ?? "" });

export const letta = new Letta({
  baseURL: process.env.LETTA_BASE_URL ?? "http://letta.internal.invalid:8283",
  apiKey: process.env.LETTA_API_KEY,
});

export const ASSIST_AGENT_ID = process.env.LETTA_ASSIST_AGENT_ID ?? "agent-00000000-0000-4000-8000-000000000000";
