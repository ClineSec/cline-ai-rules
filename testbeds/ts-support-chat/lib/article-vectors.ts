import weaviate, { type WeaviateClient } from "weaviate-client";

// Help-center articles, vectorized by Weaviate's Cohere module. Self-hosted on the support
// VM; the dev server runs it from docker compose.
const ARTICLE_HOST = "203.0.113.45";

let client: WeaviateClient | undefined;

export async function articleStore(): Promise<WeaviateClient> {
  if (client) return client;
  client =
    process.env.NODE_ENV === "development"
      ? await weaviate.connectToLocal()
      : await weaviate.connectToCustom({
          httpHost: ARTICLE_HOST,
          httpPort: 8080,
          grpcHost: ARTICLE_HOST,
          grpcPort: 50051,
          headers: { "X-Cohere-Api-Key": process.env.COHERE_API_KEY ?? "" },
        });
  return client;
}
