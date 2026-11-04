import { MilvusClient } from "@zilliz/milvus2-sdk-node";
import { QdrantClient } from "@qdrant/js-client-rest";
import weaviate, { ApiKey } from "weaviate-client";
import { ChromaClient } from "chromadb";
import { Chroma } from "@langchain/community/vectorstores/chroma";
import { Milvus } from "@langchain/community/vectorstores/milvus";

const SEARCH_URL = "https://qdrant.example.com:6333";
const LOCAL_URL = "http://127.0.0.1:6333";

export function chromaClients() {
  // ruleid: vector-db-client-without-auth-ts
  const a = new ChromaClient({ host: "chroma.example.com", port: 443, ssl: true });
  // ruleid: vector-db-client-without-auth-ts
  const b = new ChromaClient({ path: "http://203.0.113.10:8000" });
  // ok: vector-db-client-without-auth-ts
  const c = new ChromaClient({ host: "chroma.example.com", headers: { "x-chroma-token": process.env.CHROMA_TOKEN ?? "" } });
  // ok: vector-db-client-without-auth-ts
  const d = new ChromaClient({ path: "https://chroma.example.com", auth: { provider: "token", credentials: process.env.CHROMA_TOKEN } });
  // ok: vector-db-client-without-auth-ts
  const e = new ChromaClient({ host: "localhost", port: 8000 });
  // ok: vector-db-client-without-auth-ts
  const f = new ChromaClient();
  // ok: vector-db-client-without-auth-ts
  const g = new ChromaClient({ path: process.env.CHROMA_URL ?? "https://chroma.example.com" });
  return [a, b, c, d, e, f, g];
}

export function qdrantClients() {
  // ruleid: vector-db-client-without-auth-ts
  const a = new QdrantClient({ url: "https://qdrant.example.com:6333" });
  // ruleid: vector-db-client-without-auth-ts
  const b = new QdrantClient({ url: SEARCH_URL, timeout: 10_000 });
  // ruleid: vector-db-client-without-auth-ts
  const c = new QdrantClient({ host: "203.0.113.20", port: 6333 });
  // ok: vector-db-client-without-auth-ts
  const d = new QdrantClient({ url: SEARCH_URL, apiKey: process.env.QDRANT_API_KEY });
  // ok: vector-db-client-without-auth-ts
  const e = new QdrantClient({ url: LOCAL_URL });
  // ok: vector-db-client-without-auth-ts
  const f = new QdrantClient({ url: "http://qdrant:6333" });
  // ok: vector-db-client-without-auth-ts
  const g = new QdrantClient({ url: "https://3f1c.eu-central-1-0.aws.cloud.qdrant.io", apiKey: process.env.QDRANT_API_KEY });
  const shared = { url: SEARCH_URL, apiKey: process.env.QDRANT_API_KEY };
  // ok: vector-db-client-without-auth-ts
  const h = new QdrantClient({ ...shared, timeout: 5_000 });
  // ok: vector-db-client-without-auth-ts
  const i = new QdrantClient();
  return [a, b, c, d, e, f, g, h, i];
}

export async function weaviateClients() {
  // ruleid: vector-db-client-without-auth-ts
  const a = await weaviate.connectToCustom({
    httpHost: "weaviate.example.com",
    httpPort: 443,
    httpSecure: true,
    grpcHost: "grpc.weaviate.example.com",
    grpcPort: 443,
    grpcSecure: true,
    headers: { "X-OpenAI-Api-Key": process.env.OPENAI_API_KEY ?? "" },
  });
  // ruleid: vector-db-client-without-auth-ts
  const b = await weaviate.connectToLocal({ host: "203.0.113.30" });
  // ok: vector-db-client-without-auth-ts
  const c = await weaviate.connectToCustom({
    httpHost: "weaviate.example.com",
    httpSecure: true,
    grpcHost: "grpc.weaviate.example.com",
    grpcSecure: true,
    authCredentials: new ApiKey(process.env.WEAVIATE_API_KEY ?? ""),
  });
  // ok: vector-db-client-without-auth-ts
  const d = await weaviate.connectToLocal();
  // ok: vector-db-client-without-auth-ts
  const e = await weaviate.connectToLocal({ host: "weaviate" });
  // ok: vector-db-client-without-auth-ts
  const f = await weaviate.connectToLocal({ host: "weaviate.example.com", headers: { Authorization: `Bearer ${process.env.WEAVIATE_TOKEN}` } });
  // ok: vector-db-client-without-auth-ts
  const g = await weaviate.connectToWeaviateCloud("abc.c0.europe-west3.gcp.weaviate.cloud", { authCredentials: new ApiKey(process.env.WEAVIATE_API_KEY ?? "") });
  return [a, b, c, d, e, f, g];
}

export function milvusClients() {
  // ruleid: vector-db-client-without-auth-ts
  const a = new MilvusClient({ address: "milvus.example.com:19530" });
  // ruleid: vector-db-client-without-auth-ts
  const b = new MilvusClient("203.0.113.40:19530");
  // ok: vector-db-client-without-auth-ts
  const c = new MilvusClient({ address: "milvus.example.com:19530", token: process.env.MILVUS_TOKEN });
  // ok: vector-db-client-without-auth-ts
  const d = new MilvusClient("milvus.example.com:19530", true, "support", process.env.MILVUS_PASSWORD);
  // ok: vector-db-client-without-auth-ts
  const e = new MilvusClient({ address: "localhost:19530" });
  // ok: vector-db-client-without-auth-ts
  const f = new MilvusClient({ address: process.env.MILVUS_ADDRESS ?? "milvus.example.com:19530" });
  return [a, b, c, d, e, f];
}

export async function langchainStores(embeddings: any, docs: any[]) {
  // ruleid: vector-db-client-without-auth-ts
  const a = new Chroma(embeddings, { url: "https://chroma.example.com", collectionName: "macros" });
  // ruleid: vector-db-client-without-auth-ts
  const b = await Chroma.fromDocuments(docs, embeddings, { url: "http://203.0.113.43:8000", collectionName: "macros" });
  // ruleid: vector-db-client-without-auth-ts
  const c = new Milvus(embeddings, { url: "milvus.example.com:19530", collectionName: "macros" });
  // ruleid: vector-db-client-without-auth-ts
  const d = await Milvus.fromTexts(["a macro"], [{}], embeddings, { url: "https://milvus.example.com:19530" });
  // ok: vector-db-client-without-auth-ts
  const e = new Chroma(embeddings, { url: "https://chroma.example.com", clientParams: { headers: { "x-chroma-token": process.env.CHROMA_TOKEN ?? "" } } });
  // ok: vector-db-client-without-auth-ts
  const f = new Chroma(embeddings, { url: "http://localhost:8000", collectionName: "macros" });
  // ok: vector-db-client-without-auth-ts
  const g = new Milvus(embeddings, { url: "milvus.example.com:19530", username: "support", password: process.env.MILVUS_PASSWORD });
  // ok: vector-db-client-without-auth-ts
  const h = new Milvus(embeddings, { url: "milvus.example.com:19530", clientConfig: { address: "milvus.example.com:19530", token: process.env.MILVUS_TOKEN } });
  return [a, b, c, d, e, f, g, h];
}
