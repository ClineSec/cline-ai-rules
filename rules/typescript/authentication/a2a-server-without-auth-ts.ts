import express from "express";
import { DefaultRequestHandler, InMemoryTaskStore } from "@a2a-js/sdk/server";
import { UserBuilder, agentCardHandler, jsonRpcHandler, restHandler } from "@a2a-js/sdk/server/express";
import { UnauthenticatedUser } from "@a2a-js/sdk/server";
import { RecipeExecutor } from "./executor.js";
import { recipeCard } from "./card.js";
import { callerFromSession } from "./callers.js";

// Annotations stay outside the use() calls: the rule id would read as an auth middleware name.

const requestHandler = new DefaultRequestHandler(recipeCard, new InMemoryTaskStore(), new RecipeExecutor());
const app = express();

app.use("/.well-known/agent-card.json", agentCardHandler({ agentCardProvider: requestHandler }));

const rpc = jsonRpcHandler({
  requestHandler,
  // ruleid: a2a-server-without-auth-ts
  userBuilder: UserBuilder.noAuthentication,
});
app.use("/a2a/jsonrpc", rpc);

const restOptions = {
  requestHandler,
  // ruleid: a2a-server-without-auth-ts
  userBuilder: async () => new UnauthenticatedUser(),
};
app.use("/a2a/rest", restHandler(restOptions));

const partner = jsonRpcHandler({
  requestHandler,
  // A builder that never sees the request can't tell callers apart.
  // ruleid: a2a-server-without-auth-ts
  userBuilder: async () => ({ isAuthenticated: true, userName: "partner" }),
});
app.use("/a2a/partner", partner);

const internal = jsonRpcHandler({
  requestHandler,
  // Builds the caller from the request and throws when there is none.
  // ok: a2a-server-without-auth-ts
  userBuilder: async (req) => callerFromSession(req),
});
app.use("/a2a/internal", internal);

app.listen(Number(process.env.PORT ?? 4000));
