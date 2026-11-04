import express from "express";
import { DefaultRequestHandler, InMemoryTaskStore } from "@a2a-js/sdk/server";
import { UserBuilder, jsonRpcHandler } from "@a2a-js/sdk/server/express";
import { FixerExecutor, fixerCard } from "./fixerAgent.js";
import { verifyRunnerToken } from "./runnerTokens.js";

// The same agent for the deploy orchestrator on the self-hosted runners. Runner tokens are
// checked before the A2A routes, so the SDK's user builder can stay at its default.
const requestHandler = new DefaultRequestHandler(fixerCard, new InMemoryTaskStore(), new FixerExecutor());

const app = express();
app.use("/a2a", verifyRunnerToken);
app.use(
  "/a2a",
  jsonRpcHandler({
    requestHandler,
    userBuilder: UserBuilder.noAuthentication,
  }),
);
app.listen(Number(process.env.CI_FIXER_RUNNER_A2A_PORT ?? 8091));
