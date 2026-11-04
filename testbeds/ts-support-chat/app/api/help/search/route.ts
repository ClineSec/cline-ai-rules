import { openai } from "@ai-sdk/openai";
import { embed } from "ai";
import { helpIndex } from "@/lib/vector-index";
import { currentWorkspace } from "@/lib/workspace";

const PUBLIC_ONLY = { visibility: { $eq: "public" } };

async function embedQuestion(question: string) {
  const { embedding } = await embed({ model: openai.embedding("text-embedding-3-small"), value: question });
  return embedding;
}

// Help-widget search. The widget narrows by product with its own filter, e.g.
// { visibility: "public", product: "cdn" }.
export async function POST(req: Request) {
  const { question, filter } = await req.json();
  const search = {
    vector: await embedQuestion(question),
    topK: 5,
    includeMetadata: true,
    filter: filter ?? PUBLIC_ONLY,
  };
  const { matches } = await helpIndex.query(search);
  return Response.json(matches.map((m) => ({ slug: m.metadata?.slug, title: m.metadata?.title })));
}

// Agent-side search over the workspace's archived notes, kept in one namespace per workspace.
export async function GET(req: Request) {
  const workspaceId = await currentWorkspace();
  const params = new URL(req.url).searchParams;
  const { matches } = await helpIndex.namespace(`archive-${workspaceId}`).query({
    vector: await embedQuestion(params.get("q") ?? ""),
    topK: 5,
    includeMetadata: true,
    filter: JSON.parse(params.get("filter") ?? "{}"),
  });
  return Response.json(matches);
}

// The agent's own search: public articles plus their workspace's internal notes.
export async function PUT(req: Request) {
  const workspaceId = await currentWorkspace();
  const body = await req.json();
  const { matches } = await helpIndex.query({
    vector: await embedQuestion(body.question),
    topK: 8,
    includeMetadata: true,
    filter: { $or: [PUBLIC_ONLY, { workspaceId: { $eq: workspaceId } }], product: body.product },
  });
  return Response.json(matches);
}
