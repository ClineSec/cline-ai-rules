import { load } from "@langchain/core/load";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { z } from "zod";
import { saveMacroChain } from "@/lib/macro-chains";
import { currentWorkspace } from "@/lib/workspace";

// Settings > Macros > Import: paste a macro chain exported from another workspace.
export async function POST(req: Request) {
  const { name, exported } = await req.json();
  const workspaceId = await currentWorkspace();
  const chain = await load<ChatPromptTemplate>(JSON.stringify(exported));
  await saveMacroChain(workspaceId, String(name), chain);
  return Response.json({ name, inputVariables: chain.inputVariables });
}

const MACRO_SYSTEM = "You draft support replies in the workspace's tone. Never promise refunds.";

const MacroDraft = z.object({
  name: z.string().max(80),
  template: z.string().max(8000),
});

// Settings > Macros > New: the editor sends the reply template, and the chain is built here.
export async function PUT(req: Request) {
  const draft = MacroDraft.parse(await req.json());
  const workspaceId = await currentWorkspace();
  const chain = ChatPromptTemplate.fromMessages([
    ["system", MACRO_SYSTEM],
    ["human", draft.template],
  ]);
  await saveMacroChain(workspaceId, draft.name, chain);
  return Response.json({ name: draft.name, inputVariables: chain.inputVariables });
}
