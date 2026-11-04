import { MilvusClient } from "@zilliz/milvus2-sdk-node";
import { MongoClient } from "mongodb";

// Closed chat transcripts from every workspace, one Milvus collection, each row tagged with
// its workspaceId.
export const transcripts = new MilvusClient({
  address: process.env.MILVUS_ADDRESS ?? "milvus.internal.invalid:19530",
});
export const TRANSCRIPTS = "closed_transcripts";

// Escalation playbooks in MongoDB Atlas with a vector index. Each workspace writes its own;
// a few are marked shared: true for everyone.
const mongo = new MongoClient(process.env.MONGODB_URI ?? "mongodb://mongo.internal.invalid");
export const playbooks = mongo.db("support").collection("playbooks");
