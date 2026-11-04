import { ChromaClient, Search } from "chromadb";
import { Pinecone } from "@pinecone-database/pinecone";
import { QdrantClient } from "@qdrant/js-client-rest";
import { VectorStoreRetriever } from "@langchain/core/vectorstores";
import express from "express";
import { Hono } from "hono";
import { auth } from "./auth";
import { store } from "./store";

const chroma = new ChromaClient({ path: "http://chroma.internal.invalid:8000" });
const pc = new Pinecone({ apiKey: "pc-test-not-a-key" });
const index = pc.index("help-center");
const qdrant = new QdrantClient({ url: "http://qdrant.internal.invalid:6333" });
const FILTER_PRESETS: Record<string, object> = { recent: { year: { $gte: 2026 } }, all: {} };

// ---- Chroma ------------------------------------------------------------------------------

export async function POST(req: Request) {
  const { q, filters } = await req.json();
  const notes = await chroma.getCollection({ name: "notes" });
  // ruleid: vector-filter-from-user-input-ts
  return Response.json(await notes.query({ queryTexts: [q], nResults: 8, where: filters }));
}

export async function GET(request: Request) {
  const params = new URL(request.url).searchParams;
  const where = JSON.parse(params.get("where") ?? "{}");
  const notes = await chroma.getCollection({ name: "notes" });
  // ruleid: vector-filter-from-user-input-ts
  return Response.json(await notes.get({ where, limit: 20 }));
}

export async function DELETE(req: Request) {
  const body = await req.json();
  const notesCollection = await chroma.getCollection({ name: "notes" });
  // ruleid: vector-filter-from-user-input-ts
  await notesCollection.delete({ where: body.where });
  return new Response(null, { status: 204 });
}

export async function PATCH(req: Request) {
  const session = await auth();
  const body = await req.json();
  const notes = await chroma.getCollection({ name: "notes" });
  // The request's keys come last, so { workspaceId: "other-ws" } replaces the server's.
  // ruleid: vector-filter-from-user-input-ts
  const res = await notes.query({ queryTexts: [body.q], where: { workspaceId: session.workspaceId, ...body.filters } });
  // ok: vector-filter-from-user-input-ts
  await notes.query({ queryTexts: [body.q], where: { ...body.filters, workspaceId: session.workspaceId } });
  // ok: vector-filter-from-user-input-ts
  await notes.query({ queryTexts: [body.q], where: { $and: [{ workspaceId: session.workspaceId }, { topic: body.topic }] } });
  // whereDocument only matches document text, and is ANDed with the server's where.
  // ok: vector-filter-from-user-input-ts
  await notes.query({ queryTexts: [body.q], where: { workspaceId: session.workspaceId }, whereDocument: body.contains });
  // ok: vector-filter-from-user-input-ts
  await notes.query({ queryTexts: [body.q], where: FILTER_PRESETS[body.preset] });
  // ruleid: vector-filter-from-user-input-ts
  await notes.query({ queryTexts: [body.q], where: { workspaceId: session.workspaceId, [body.field]: body.value } });
  // The server's key comes last, so it wins.
  // ok: vector-filter-from-user-input-ts
  await notes.query({ queryTexts: [body.q], where: { [body.field]: body.value, workspaceId: session.workspaceId } });
  const TOPIC_FIELD = "topic";
  // ok: vector-filter-from-user-input-ts
  await notes.query({ queryTexts: [body.q], where: { workspaceId: session.workspaceId, [TOPIC_FIELD]: body.value } });
  // ruleid: vector-filter-from-user-input-ts
  await notes.search(new Search().where(body.where).limit(10));
  return Response.json(res);
}

// ---- Pinecone ----------------------------------------------------------------------------

const app = express();
app.use(express.json());

app.post("/kb/search", async (req, res) => {
  // ruleid: vector-filter-from-user-input-ts
  const result = await index.query({ vector: req.body.vector, topK: 5, filter: req.body.filter, includeMetadata: true });
  res.json(result);
});

app.post("/kb/records", async (req, res) => {
  const { text, filter } = req.body;
  const result = await index.searchRecords({
    // ruleid: vector-filter-from-user-input-ts
    query: { topK: 5, inputs: { text }, filter },
  });
  res.json(result);
});

app.post("/kb/purge", async (req, res) => {
  // ruleid: vector-filter-from-user-input-ts
  await index.deleteMany({ filter: req.body.filter });
  res.sendStatus(204);
});

app.post("/kb/tenant", async (req, res) => {
  const session = await auth();
  // The namespace is the caller's own, so the filter only narrows inside it.
  // ok: vector-filter-from-user-input-ts
  const result = await index.namespace(session.orgId).query({ vector: req.body.vector, topK: 5, filter: req.body.filter });
  const ns = index.namespace(`org-${session.orgId}`);
  // ok: vector-filter-from-user-input-ts
  await ns.query({ vector: req.body.vector, topK: 5, filter: req.body.filter });
  // ok: vector-filter-from-user-input-ts
  await index.query({ vector: req.body.vector, topK: 5, filter: { orgId: session.orgId, topic: req.body.topic } });
  res.json(result);
});

app.post("/kb/fixed-namespace", async (req, res) => {
  // ruleid: vector-filter-from-user-input-ts
  const result = await index.namespace("help-center").query({ vector: req.body.vector, topK: 5, filter: req.body.filter });
  res.json(result);
});

// ---- Qdrant ------------------------------------------------------------------------------

const hono = new Hono();

hono.post("/docs/search", async (c) => {
  const body = await c.req.json();
  // ruleid: vector-filter-from-user-input-ts
  const result = await qdrant.query("docs", { query: body.vector, filter: body.filter, limit: 5 });
  return c.json(result);
});

hono.post("/docs/purge", async (c) => {
  const body = await c.req.json();
  // ruleid: vector-filter-from-user-input-ts
  await qdrant.delete("docs", { filter: body.filter, wait: true });
  return c.body(null, 204);
});

hono.post("/docs/scoped", async (c) => {
  const session = await auth();
  const body = await c.req.json();
  const result = await qdrant.scroll("docs", {
    // ok: vector-filter-from-user-input-ts
    filter: { must: [{ key: "org_id", match: { value: session.orgId } }, { key: "topic", match: { value: body.topic } }] },
  });
  // ok: vector-filter-from-user-input-ts
  await qdrant.count("docs", { filter: body.filter, shard_key: session.orgId });
  return c.json(result);
});

// ---- LangChain.js ------------------------------------------------------------------------

export async function searchPlaybooks(req: Request) {
  const body = await req.json();
  // ruleid: vector-filter-from-user-input-ts
  const docs = await store.similaritySearch(body.query, 4, body.filter);
  // ruleid: vector-filter-from-user-input-ts
  const retriever = store.asRetriever({ k: 6, filter: body.filter });
  // ruleid: vector-filter-from-user-input-ts
  const mmr = await store.maxMarginalRelevanceSearch(body.query, { k: 4, fetchK: 20, filter: body.filter });
  return [docs, retriever, mmr];
}

export async function searchPlaybooksScoped(req: Request) {
  const session = await auth();
  const body = await req.json();
  // ok: vector-filter-from-user-input-ts
  const retriever = new VectorStoreRetriever({ vectorStore: store, k: 6, filter: { orgId: session.orgId, topic: body.topic } });
  // ok: vector-filter-from-user-input-ts
  const docs = await store.similaritySearch(body.query, 4, scopedFilter(session.orgId, body.filter));
  return [retriever, docs];
}

function scopedFilter(orgId: string, extra: Record<string, unknown>) {
  return { $and: [{ orgId }, extra] };
}

export async function searchWithRetriever(req: Request, retriever: VectorStoreRetriever) {
  const { query, filter } = await req.json();
  // ruleid: vector-filter-from-user-input-ts
  retriever.filter = filter;
  return retriever.invoke(query);
}

export async function searchWithOptions(req: Request) {
  const session = await auth();
  const body = await req.json();
  // ruleid: vector-filter-from-user-input-ts
  const search = { vector: body.vector, topK: 5, includeMetadata: true, filter: body.filter ?? { visibility: "public" } };
  const { matches } = await index.query(search);
  // ok: vector-filter-from-user-input-ts
  const scoped = { vector: body.vector, topK: 5, filter: { orgId: session.orgId, topic: body.topic } };
  await index.query(scoped);
  const notes = await chroma.getCollection({ name: "notes" });
  // ruleid: vector-filter-from-user-input-ts
  const args = { queryTexts: [body.q], where: body.where };
  await notes.query(args);
  // ruleid: vector-filter-from-user-input-ts
  const opts = { filter: body.filter, limit: 5 };
  await qdrant.scroll("docs", opts);
  return matches;
}

export async function spreadOfExpressionLast(req: Request) {
  const session = await auth();
  const body = await req.json();
  // ruleid: vector-filter-from-user-input-ts
  return index.query({ vector: body.vector, topK: 5, filter: { orgId: session.orgId, ...(body.filters ?? {}) } });
}

export async function retagByFilter(req: Request, prefs: { update(o: object): void }) {
  const body = await req.json();
  // ruleid: vector-filter-from-user-input-ts
  await index.update({ filter: body.filter, metadata: { reviewed: true } });
  // A preferences store that keeps the user's last filter.
  // ok: vector-filter-from-user-input-ts
  prefs.update({ filter: body.filter });
}

export async function perRequestStore(req: Request, embeddings: never, pineconeIndex: never) {
  const body = await req.json();
  const { Chroma } = await import("@langchain/community/vectorstores/chroma");
  const { PineconeStore } = await import("@langchain/pinecone");
  // ruleid: vector-filter-from-user-input-ts
  const chromaStore = new Chroma(embeddings, { collectionName: "notes", filter: body.filter });
  // ruleid: vector-filter-from-user-input-ts
  const pineStore = await PineconeStore.fromExistingIndex(embeddings, { pineconeIndex, filter: body.filter });
  return [chromaStore, pineStore];
}

app.post("/kb/by-field", async (req, res) => {
  const { field, value } = req.body;
  // ruleid: vector-filter-from-user-input-ts
  const a = await index.query({ vector: req.body.vector, topK: 5, filter: { orgId: "acme", [field]: value } });
  // ruleid: vector-filter-from-user-input-ts
  const b = await index.query({ vector: req.body.vector, topK: 5, filter: { orgId: "acme", [req.body.field]: req.body.value } });
  res.json([a, b]);
});

// ---- Milvus ------------------------------------------------------------------------------

import { MilvusClient } from "@zilliz/milvus2-sdk-node";

const milvus = new MilvusClient({ address: "milvus.internal.invalid:19530" });

app.post("/tickets/search", async (req, res) => {
  const { vector, filter } = req.body;
  // ruleid: vector-filter-from-user-input-ts
  const hits = await milvus.search({ collection_name: "tickets", data: [vector], limit: 5, filter });
  // ruleid: vector-filter-from-user-input-ts
  const rows = await milvus.query({ collection_name: "tickets", expr: req.body.expr, output_fields: ["id"] });
  // ruleid: vector-filter-from-user-input-ts
  await milvus.delete({ collection_name: "tickets", filter: String(req.query.filter).trim() });
  res.json({ hits, rows });
});

app.post("/tickets/by-topic", async (req, res) => {
  const session = await auth(req);
  // Request text pasted into the expression can close the quote and add `or ...`.
  // ruleid: vector-filter-from-user-input-ts
  await milvus.search({ collection_name: "tickets", data: [req.body.vector], filter: `org_id == "${session.orgId}" and topic == "${req.body.topic}"` });
  // The server's expression with the request's value bound as a template parameter.
  // ok: vector-filter-from-user-input-ts
  await milvus.search({ collection_name: "tickets", data: [req.body.vector], filter: "org_id == {org} and topic == {topic}", exprValues: { org: session.orgId, topic: req.body.topic } });
  // A JSON-quoted value can't leave its string.
  // ok: vector-filter-from-user-input-ts
  const hits = await milvus.count({ collection_name: "tickets", filter: `org_id == ${JSON.stringify(session.orgId)} and topic == ${JSON.stringify(req.body.topic)}` });
  res.json(hits);
});

app.post("/tickets/hybrid", async (req, res) => {
  const session = await auth(req);
  const { dense, sparse, expr } = req.body;
  const hits = await milvus.hybridSearch({
    collection_name: "tickets",
    data: [
      // ruleid: vector-filter-from-user-input-ts
      { anns_field: "dense", data: [dense], expr },
      // ok: vector-filter-from-user-input-ts
      { anns_field: "sparse", data: [sparse], expr: "org_id == {org} and topic == {topic}", exprValues: { org: session.orgId, topic: req.body.topic } },
    ],
    limit: 5,
  });
  const subSearches = [
    // ruleid: vector-filter-from-user-input-ts
    { anns_field: "dense", data: [dense], expr: req.body.denseExpr },
    // ok: vector-filter-from-user-input-ts
    { anns_field: "sparse", data: [sparse], expr: `org_id == ${JSON.stringify(session.orgId)}` },
  ];
  const more = await milvus.hybridSearch({ collection_name: "tickets", data: subSearches, limit: 5 });
  // A plain array that never reaches hybridSearch.
  // ok: vector-filter-from-user-input-ts
  const audit = [{ step: "hybrid", expr: req.body.denseExpr }];
  res.json({ hits, more, audit });
});

// ---- MongoDB Atlas Vector Search ---------------------------------------------------------

import { MongoClient } from "mongodb";
import { MongoDBAtlasVectorSearch } from "@langchain/mongodb";

const articles = new MongoClient("mongodb://mongo.internal.invalid").db("kb").collection("articles");

app.post("/articles/search", async (req, res) => {
  const session = await auth(req);
  // ruleid: vector-filter-from-user-input-ts
  const open = await articles.aggregate([{ $vectorSearch: { index: "vector_index", path: "embedding", queryVector: req.body.vector, numCandidates: 100, limit: 5, filter: req.body.filter } }]).toArray();
  const pipeline = [
    // ok: vector-filter-from-user-input-ts
    { $vectorSearch: { index: "vector_index", path: "embedding", queryVector: req.body.vector, numCandidates: 100, limit: 5, filter: { orgId: session.orgId, topic: req.body.topic } } },
    // A $match after the stage only narrows what it returned.
    // ok: vector-filter-from-user-input-ts
    { $match: req.body.filter },
  ];
  res.json([open, await articles.aggregate(pipeline).toArray()]);
});

export async function askArticles(req: Request, atlas: MongoDBAtlasVectorSearch) {
  const session = await auth(req);
  const body = await req.json();
  // ruleid: vector-filter-from-user-input-ts
  const loose = await atlas.similaritySearch(body.q, 4, { preFilter: body.filter });
  // ruleid: vector-filter-from-user-input-ts
  const viaRetriever = await atlas.asRetriever({ k: 4, filter: { preFilter: body.preFilter } }).invoke(body.q);
  // ok: vector-filter-from-user-input-ts
  const scoped = await atlas.similaritySearch(body.q, 4, { preFilter: { orgId: { $eq: session.orgId }, topic: body.topic } });
  // ruleid: vector-filter-from-user-input-ts
  const byFacet = await atlas.similaritySearch(body.q, 4, { preFilter: { orgId: { $eq: session.orgId }, [body.facet]: body.value } });
  // ok: vector-filter-from-user-input-ts
  const byFacetScoped = await atlas.similaritySearch(body.q, 4, { preFilter: { [body.facet]: body.value, orgId: { $eq: session.orgId } } });
  const stages = [
    // ruleid: vector-filter-from-user-input-ts
    { $vectorSearch: { index: "vector_index", path: "embedding", queryVector: body.vector, limit: 5, filter: { orgId: session.orgId, [body.facet]: body.value } } },
  ];
  await articles.aggregate(stages).toArray();
  return Response.json([loose, viaRetriever, scoped, byFacet, byFacetScoped]);
}
