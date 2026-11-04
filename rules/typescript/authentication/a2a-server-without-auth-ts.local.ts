// A local-only agent for the desktop app, on loopback.
import express from "express";
import { UserBuilder, jsonRpcHandler } from "@a2a-js/sdk/server/express";
import { requestHandler } from "./handler.js";

const HOST = process.env.AGENT_HOST ?? "127.0.0.1";
const app = express();
app.use(
  jsonRpcHandler({
    requestHandler,
    // ok: a2a-server-without-auth-ts
    userBuilder: UserBuilder.noAuthentication,
  }),
);
app.listen(4100, HOST);
