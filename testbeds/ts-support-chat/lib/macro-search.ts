import { QdrantClient } from "@qdrant/js-client-rest";

// Canned replies ("macros") embedded once a night by the content team's job. Agents search
// them from the reply drafter; the cluster is shared with the help-center team.
const MACRO_INDEX_URL = "https://vectors.example.com:6333";
export const MACRO_COLLECTION = "support_macros";

export const macroIndex = new QdrantClient({ url: MACRO_INDEX_URL, timeout: 15_000 });

// Draft macros from the content team stay in their own, keyed collection until reviewed.
export const draftMacroIndex = new QdrantClient({
  url: MACRO_INDEX_URL,
  apiKey: process.env.QDRANT_DRAFTS_KEY,
  timeout: 15_000,
});

export async function similarMacros(vector: number[], limit = 5): Promise<string[]> {
  const found = await macroIndex.query(MACRO_COLLECTION, { query: vector, limit, with_payload: true });
  return found.points.map((point) => String(point.payload?.title ?? ""));
}
