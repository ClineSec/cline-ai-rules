// A team's own API-key check in front of the MCP route counts as authentication.
import type { NextFunction, Request, Response } from "express";
import { createMcpExpressApp } from "@modelcontextprotocol/express";

function checkApiKey(req: Request, res: Response, next: NextFunction) {
  if (req.get("x-api-key") !== process.env.NOTES_API_KEY) return res.status(401).end();
  next();
}

// ok: mcp-server-exposed-without-auth-ts
const app = createMcpExpressApp({ host: "0.0.0.0" });
app.post("/mcp", checkApiKey, handleMcp);
// ok: mcp-server-exposed-without-auth-ts
app.listen(3000, "0.0.0.0");
