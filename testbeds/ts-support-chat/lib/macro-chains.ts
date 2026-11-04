import { load } from "@langchain/core/load";
import type { ChatPromptTemplate } from "@langchain/core/prompts";
import { pull } from "langchain/hub/node";
import { prisma } from "@/lib/db";

// Reply macros saved as LangChain chains (prompt plus the drafting model). A saved chain
// names its provider key as a secret, and the key lives in the server's environment.
const RESTORE_OPTIONS = {
  secretsFromEnv: true,
  maxDepth: 30,
};

// Prompts the support-ops team maintains in LangSmith.
const REPLY_DRAFTER_PROMPT = "support-ops/reply-drafter";
const ESCALATION_SUMMARY_PROMPT = "support-ops/escalation-summary:3f9a1c7e";

export async function saveMacroChain(workspaceId: string, name: string, chain: ChatPromptTemplate) {
  await prisma.macroChain.create({ data: { workspaceId, name, manifest: JSON.stringify(chain) } });
}

export async function restoreMacroChain(macroId: string) {
  const row = await prisma.macroChain.findUniqueOrThrow({ where: { id: macroId } });
  return load<ChatPromptTemplate>(row.manifest, RESTORE_OPTIONS);
}

/** A teammate's draft macro, previewed with only the key the drafting model needs. */
export async function previewMacroChain(manifest: string) {
  return load<ChatPromptTemplate>(manifest, {
    secretsMap: { OPENAI_API_KEY: process.env.OPENAI_API_KEY ?? "" },
  });
}

export async function replyDrafter() {
  return pull<ChatPromptTemplate>(REPLY_DRAFTER_PROMPT, { includeModel: true });
}

export async function escalationSummarizer() {
  // Pinned to the commit support-ops signed off on.
  return pull<ChatPromptTemplate>(ESCALATION_SUMMARY_PROMPT, { includeModel: true });
}
