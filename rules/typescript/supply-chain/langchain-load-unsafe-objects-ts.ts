import { load } from "@langchain/core/load";
import * as classicLoad from "langchain/load";
import { load as legacyLoad } from "langchain/load";
import { pull } from "langchain/hub/node";
import type { ChatPromptTemplate } from "@langchain/core/prompts";

export async function restoreChain(text: string) {
  return load(text, {
    // ruleid: langchain-load-unsafe-objects-ts
    secretsFromEnv: true,
  });
}

// ruleid: langchain-load-unsafe-objects-ts
const RESTORE_OPTIONS = { secretsFromEnv: true, maxDepth: 20 };

export async function restoreWithOptions(text: string) {
  return load(text, RESTORE_OPTIONS);
}

export async function restoreWithEnvMap(text: string) {
  // ruleid: langchain-load-unsafe-objects-ts
  return load(text, { secretsMap: process.env as Record<string, string> });
}

export async function restoreWithEnvSpread(text: string) {
  // ruleid: langchain-load-unsafe-objects-ts
  return load(text, { secretsMap: { ...process.env, EXTRA: "x" } });
}

export async function restoreClassic(text: string) {
  // ruleid: langchain-load-unsafe-objects-ts
  return classicLoad.load(text, {}, {}, {}, true);
}

export async function restoreLegacyAlias(text: string) {
  // ruleid: langchain-load-unsafe-objects-ts
  return legacyLoad(text, process.env);
}

export async function pullDigestPrompt() {
  // ruleid: langchain-load-unsafe-objects-ts
  return pull<ChatPromptTemplate>("support-team/reply-drafter", { includeModel: true });
}

export async function pullAwaitedGeneric() {
  // ruleid: langchain-load-unsafe-objects-ts
  const prompt = await pull<ChatPromptTemplate>("support-team/macro-writer", {
    includeModel: true,
  });
  return prompt;
}

const PULL_OPTIONS = { includeModel: true, skipCache: false };

export async function pullWithSharedOptions(name: string) {
  // ruleid: langchain-load-unsafe-objects-ts
  return pull(name, PULL_OPTIONS);
}

export async function pullWithEnvSecrets() {
  return pull("support-team/reply-drafter:5c9e2a7b", {
    // ruleid: langchain-load-unsafe-objects-ts
    secretsFromEnv: true,
  });
}

// --- near misses ------------------------------------------------------------------------

export async function restoreDefaults(text: string) {
  // ok: langchain-load-unsafe-objects-ts
  return load(text);
}

export async function restoreWithOneKey(text: string) {
  // ok: langchain-load-unsafe-objects-ts
  return load(text, { secretsMap: { OPENAI_API_KEY: process.env.OPENAI_API_KEY ?? "" }, secretsFromEnv: false });
}

export async function restoreClassicDefaults(text: string) {
  // ok: langchain-load-unsafe-objects-ts
  return classicLoad.load(text, {}, {}, {}, false);
}

const PINNED_DRAFTER = "support-team/reply-drafter:5c9e2a7b";

export async function pullPinned() {
  // ok: langchain-load-unsafe-objects-ts
  return pull(PINNED_DRAFTER, { includeModel: true });
}

export async function pullPromptOnly() {
  // ok: langchain-load-unsafe-objects-ts
  return pull("support-team/reply-drafter");
}

export function featureFlags() {
  // A different library's option of the same name.
  // ok: langchain-load-unsafe-objects-ts
  return { includeModel: true, secretsFromEnvLabel: "on" };
}
