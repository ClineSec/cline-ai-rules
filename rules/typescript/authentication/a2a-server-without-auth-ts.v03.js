// @a2a-js/sdk 0.3: A2AExpressApp defaults to UserBuilder.noAuthentication.
const express = require("express");
const { A2AExpressApp } = require("@a2a-js/sdk/server/express");
const { handler } = require("./handler");
const { verifyPartnerToken } = require("./partners");

const appBuilder = new A2AExpressApp(handler);
// ruleid: a2a-server-without-auth-ts
const app = appBuilder.setupRoutes(express(), "/a2a");

// Middlewares passed to setupRoutes run before the A2A routes.
const guarded = new A2AExpressApp(handler);
// ok: a2a-server-without-auth-ts
guarded.setupRoutes(express(), "/partner", [verifyPartnerToken]);

app.listen(3000);
