import { openai } from "@ai-sdk/openai";
import { generateText, type ModelMessage } from "ai";
import { currentWorkspace } from "@/lib/workspace";

const ESCALATION_INSTRUCTIONS =
  "Decide whether this support conversation needs a human. Reply with ESCALATE or CONTINUE and one sentence of reasoning.";

// Called by the chat widget after every customer turn.
export async function POST(req: Request) {
  const workspaceId = await currentWorkspace();
  const { conversation }: { conversation: ModelMessage[] } = await req.json();
  const turns = conversation.slice(-12);

  console.info(`[escalation] workspace=${workspaceId} turns=${turns.length}`);
  console.info("[escalation] model input", JSON.stringify(turns));

  const { text, usage } = await generateText({
    model: openai("gpt-4.1-mini"),
    instructions: ESCALATION_INSTRUCTIONS,
    messages: turns,
  });

  console.info(`[escalation] decision=${text.split(/\s/, 1)[0]} tokens=${usage.totalTokens}`);
  return Response.json({ escalate: text.startsWith("ESCALATE") });
}
