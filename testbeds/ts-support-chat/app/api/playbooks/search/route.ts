import { MongoDBAtlasVectorSearch } from "@langchain/mongodb";
import { OpenAIEmbeddings } from "@langchain/openai";
import { playbooks } from "@/lib/transcript-index";
import { currentWorkspace } from "@/lib/workspace";

const embeddings = new OpenAIEmbeddings({ model: "text-embedding-3-small" });

function playbookStore() {
  return new MongoDBAtlasVectorSearch(embeddings, {
    collection: playbooks,
    indexName: "playbook_vectors",
    textKey: "body",
    embeddingKey: "embedding",
  });
}

// Escalation playbook search from the ticket sidebar. The sidebar sends its tag chips as a
// filter that already includes { workspaceId }.
export async function POST(req: Request) {
  const body = await req.json();
  const queryVector = await embeddings.embedQuery(body.question);
  const found = await playbooks
    .aggregate([
      {
        $vectorSearch: {
          index: "playbook_vectors",
          path: "embedding",
          queryVector,
          numCandidates: 150,
          limit: 5,
          filter: body.filter,
        },
      },
      { $project: { embedding: 0 } },
    ])
    .toArray();
  return Response.json(found);
}

// Facet chips: one field and value picked in the sidebar, on top of the workspace scope.
export async function PATCH(req: Request) {
  const workspaceId = await currentWorkspace();
  const body = await req.json();
  const scope = { workspaceId: { $eq: workspaceId } };
  const store = playbookStore();
  const docs = await store.similaritySearch(body.question, 4, { preFilter: { ...scope, [body.facet]: body.value } });
  return Response.json(docs.map((d) => d.pageContent));
}

// The suggestion strip: the workspace's playbooks plus shared ones, narrowed by product.
export async function GET(req: Request) {
  const workspaceId = await currentWorkspace();
  const params = new URL(req.url).searchParams;
  const docs = await playbookStore().similaritySearch(params.get("q") ?? "", 4, {
    preFilter: {
      $or: [{ workspaceId: { $eq: workspaceId } }, { shared: { $eq: true } }],
      product: { $eq: params.get("product") ?? "core" },
    },
  });
  return Response.json(docs.map((d) => d.pageContent));
}
