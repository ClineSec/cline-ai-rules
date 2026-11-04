// The SDK's bearer-token middleware guards the endpoint, so binding every interface is fine.
import { createMcpExpressApp, requireBearerAuth } from "@modelcontextprotocol/express";

import { verifier } from "./verifier.js";

// ok: mcp-server-exposed-without-auth-ts
const app = createMcpExpressApp({ host: "0.0.0.0", allowedHosts: ["notes.example.com"] });
app.use("/mcp", requireBearerAuth({ verifier, requiredScopes: ["notes:read"] }));
// ok: mcp-server-exposed-without-auth-ts
app.listen(3000, "0.0.0.0");
