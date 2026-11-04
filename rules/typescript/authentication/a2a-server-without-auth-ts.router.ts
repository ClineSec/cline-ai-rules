// Exported router: the server that mounts it decides what runs in front.
import { Router } from "express";
import { UserBuilder, jsonRpcHandler } from "@a2a-js/sdk/server/express";
import { requestHandler } from "./handler.js";

export const a2aRouter = Router();
a2aRouter.use(
  jsonRpcHandler({
    requestHandler,
    // ok: a2a-server-without-auth-ts
    userBuilder: UserBuilder.noAuthentication,
  }),
);
