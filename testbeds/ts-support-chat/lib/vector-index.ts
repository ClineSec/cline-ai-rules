import { Pinecone } from "@pinecone-database/pinecone";
import { ChromaClient } from "chromadb";

// Help-center articles and each workspace's internal notes share one Pinecone index. Public
// articles carry `visibility: "public"`; internal notes carry their `workspaceId`.
export type ArticleMeta = {
  slug: string;
  title: string;
  visibility: "public" | "internal";
  workspaceId?: string;
  product?: string;
};

const pinecone = new Pinecone({ apiKey: process.env.PINECONE_API_KEY ?? "" });

export const helpIndex = pinecone.index<ArticleMeta>({ name: "help-center" });

const chroma = new ChromaClient({ path: process.env.CHROMA_URL ?? "http://chroma.internal.invalid:8000" });

/** Reply macros written by each workspace's leads, tagged with their workspaceId. */
export function macroCollection() {
  return chroma.getOrCreateCollection({ name: "reply-macros" });
}
