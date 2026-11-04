import express from "express";
import { DefaultRequestHandler, InMemoryTaskStore } from "@a2a-js/sdk/server";
import { UserBuilder, agentCardHandler, jsonRpcHandler, restHandler } from "@a2a-js/sdk/server/express";
import { FixerExecutor, fixerCard } from "./fixerAgent.js";

// Exposes the CI fixer to the other agents in the org over A2A, next to the webhook server.
const A2A_PORT = Number(process.env.CI_FIXER_A2A_PORT ?? 8090);

const requestHandler = new DefaultRequestHandler(fixerCard, new InMemoryTaskStore(), new FixerExecutor());

// Shared by the JSON-RPC and REST transports.
const transportOptions = {
  requestHandler,
  userBuilder: UserBuilder.noAuthentication,
};

const app = express();
app.use("/.well-known/agent-card.json", agentCardHandler({ agentCardProvider: requestHandler }));
app.use("/a2a/jsonrpc", jsonRpcHandler(transportOptions));
app.use("/a2a/rest", restHandler(transportOptions));
app.get("/healthz", (_req, res) => {
  res.send("ok");
});

app.listen(A2A_PORT, () => {
  console.log(`ci-fixer A2A agent on :${A2A_PORT}`);
});
