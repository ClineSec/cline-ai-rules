import { Chroma } from "@langchain/community/vectorstores/chroma";
import { OpenAIEmbeddings } from "@langchain/openai";
import { macroCollection } from "@/lib/vector-index";
import { currentWorkspace } from "@/lib/workspace";

const macroStore = new Chroma(new OpenAIEmbeddings({ model: "text-embedding-3-small" }), {
  collectionName: "reply-macros",
  url: process.env.CHROMA_URL ?? "http://chroma.internal.invalid:8000",
});

function toSuggestion(d: { metadata: Record<string, string>; pageContent: string }) {
  return { id: d.metadata.macroId, title: d.metadata.title, body: d.pageContent };
}

// Suggested macros for the reply the agent is drafting. The composer sends the agent's
// workspace and the ticket's locale as the filter.
export async function POST(req: Request) {
  const body = await req.json();
  const retriever = macroStore.asRetriever(3, body.filter);
  const docs = await retriever.invoke(body.draft);
  return Response.json(docs.map(toSuggestion));
}

// Macro library search with the composer's facet chips (locale, product).
export async function GET(req: Request) {
  const workspaceId = await currentWorkspace();
  const params = new URL(req.url).searchParams;
  const facets = Object.fromEntries(["locale", "product"].flatMap((k) => (params.has(k) ? [[k, params.get(k)]] : [])));
  const macros = await macroCollection();
  const res = await macros.query({
    queryTexts: [params.get("q") ?? ""],
    nResults: 10,
    where: Object.keys(facets).length ? { $and: [{ workspaceId }, facets] } : { workspaceId },
  });
  return Response.json(res);
}
