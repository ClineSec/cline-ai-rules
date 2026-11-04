import { openai } from "@ai-sdk/openai";
import { embed } from "ai";
import { TRANSCRIPTS, transcripts } from "@/lib/transcript-index";
import { currentWorkspace } from "@/lib/workspace";

async function embedText(value: string) {
  const { embedding } = await embed({ model: openai.embedding("text-embedding-3-small"), value });
  return embedding;
}

// "Similar past chats" in the agent console. Power users can type a Milvus expression
// (channel == "email" and csat < 3); the console pre-fills it with the agent's workspace.
export async function POST(req: Request) {
  const workspaceId = await currentWorkspace();
  const body = await req.json();
  const expression = String(body.expression ?? "").trim() || `workspaceId == "${workspaceId}"`;
  const results = await transcripts.search({
    collection_name: TRANSCRIPTS,
    data: [await embedText(body.text)],
    limit: 8,
    filter: expression,
    output_fields: ["chatId", "summary", "csat"],
  });
  return Response.json(results.results);
}

// The CSAT drill-down: the console's channel and score pickers, bound as template values.
export async function GET(req: Request) {
  const workspaceId = await currentWorkspace();
  const params = new URL(req.url).searchParams;
  const rows = await transcripts.query({
    collection_name: TRANSCRIPTS,
    filter: "workspaceId == {ws} and channel == {channel} and csat <= {maxCsat}",
    exprValues: { ws: workspaceId, channel: params.get("channel") ?? "chat", maxCsat: Number(params.get("maxCsat") ?? 5) },
    output_fields: ["chatId", "summary", "csat"],
    limit: 50,
  });
  return Response.json(rows.data);
}
