import { Chroma } from "@langchain/community/vectorstores/chroma";
import { OpenAIEmbeddings } from "@langchain/openai";

// Refund and warranty policies, chunked by the policy team's sync job. The agent-assist
// drafter quotes from here, so answers should only ever cite approved policy text.
const embeddings = new OpenAIEmbeddings({ model: "text-embedding-3-small" });

export const policyStore = new Chroma(embeddings, {
  url: "https://chroma.example.com",
  collectionName: "support_policies",
});

// The legal team's annotated copy goes through their token proxy.
export const annotatedPolicyStore = new Chroma(embeddings, {
  url: "https://chroma-legal.example.com",
  collectionName: "support_policies_annotated",
  clientParams: { headers: { "x-chroma-token": process.env.CHROMA_LEGAL_TOKEN ?? "" } },
});

export async function quotePolicy(question: string): Promise<string[]> {
  const hits = await policyStore.similaritySearch(question, 3);
  return hits.map((doc) => doc.pageContent);
}
