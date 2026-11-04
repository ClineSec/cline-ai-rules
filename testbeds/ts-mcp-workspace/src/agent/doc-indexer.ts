// Docs indexer on LangChain's classic AgentExecutor: walks the docs folder and tags each page.
import { AgentExecutor, createToolCallingAgent } from "@langchain/classic/agents";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { tool } from "@langchain/core/tools";
import { ChatOpenAI } from "@langchain/openai";
import { z } from "zod";

const DOC_PAGES: Record<string, string> = {
  "getting-started.md": "How to install and run the workspace server.",
  "tools.md": "The tools the server exposes.",
};

const readPage = tool(async ({ page }) => DOC_PAGES[page] ?? "No such page.", {
  name: "read_page",
  description: "Read one page of the docs folder by file name",
  schema: z.object({ page: z.string() }),
});

const prompt = ChatPromptTemplate.fromMessages([
  ["system", "You tag each docs page with one topic: setup, tools, or reference."],
  ["human", "{input}"],
  ["placeholder", "{agent_scratchpad}"],
]);

// The full re-index visits every page; the cap of 15 cut it short.
const FULL_REINDEX = { maxIterations: Infinity, returnIntermediateSteps: true };
// null falls back to the default of 15, so this one stays capped.
const SPOT_CHECK = { maxIterations: null, returnIntermediateSteps: false };

async function executor(limits: typeof FULL_REINDEX | typeof SPOT_CHECK) {
  const llm = new ChatOpenAI({ model: "gpt-5", temperature: 0 });
  const agent = await createToolCallingAgent({ llm, tools: [readPage], prompt });
  return new AgentExecutor({ agent, tools: [readPage], ...limits });
}

export async function reindexDocs() {
  return (await executor(FULL_REINDEX)).invoke({ input: "Tag every page in the docs folder." });
}

export async function spotCheck(page: string) {
  return (await executor(SPOT_CHECK)).invoke({ input: `Tag the page ${page}.` });
}
