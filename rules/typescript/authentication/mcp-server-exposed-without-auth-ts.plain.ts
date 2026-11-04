// A web app with no MCP server in it: binding every interface is its own business.
import express from "express";

const app = express();
app.get("/healthz", (_req, res) => res.send("ok"));
// ok: mcp-server-exposed-without-auth-ts
app.listen(8080, "0.0.0.0");
