// Bearer tokens are checked before the A2A routes.
import express from "express";
import { UserBuilder, jsonRpcHandler } from "@a2a-js/sdk/server/express";
import { requestHandler } from "./handler.js";
import { requireBearer } from "./tokens.js";

const app = express();
app.use("/a2a", requireBearerAuth({ verifier: requireBearer }));
app.use(
  "/a2a",
  jsonRpcHandler({
    requestHandler,
    // ok: a2a-server-without-auth-ts
    userBuilder: UserBuilder.noAuthentication,
  }),
);
app.listen(4000);
