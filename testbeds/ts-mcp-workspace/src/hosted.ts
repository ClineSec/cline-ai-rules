// The hosted deployment: the same tools for the team's cloud IDE, behind the company's OAuth
// server. Every request needs a bearer token issued for this server.
import { createMcpExpressApp, requireBearerAuth } from "@modelcontextprotocol/express";
import type { OAuthTokenVerifier } from "@modelcontextprotocol/express";
import { NodeStreamableHTTPServerTransport } from "@modelcontextprotocol/node";
import { McpServer } from "@modelcontextprotocol/server";

import { registerGitTools } from "./tools/git.js";
import { registerSearchTools } from "./tools/search.js";

const ISSUER = process.env.WORKSPACE_ISSUER ?? "https://auth.example.com";
const RESOURCE = process.env.WORKSPACE_RESOURCE ?? "https://workspace.example.com/mcp";

const verifier: OAuthTokenVerifier = {
  async verifyAccessToken(token) {
    const resp = await fetch(`${ISSUER}/oauth/introspect`, {
      method: "POST",
      body: new URLSearchParams({ token }),
    });
    const claims = (await resp.json()) as { active: boolean; aud?: string; client_id: string; scope?: string; exp?: number };
    if (!claims.active || claims.aud !== RESOURCE) throw new Error("invalid token");
    return { token, clientId: claims.client_id, scopes: (claims.scope ?? "").split(" "), expiresAt: claims.exp };
  },
};

const app = createMcpExpressApp({ host: "0.0.0.0", allowedHosts: ["workspace.example.com"] });
app.use("/mcp", requireBearerAuth({ verifier, requiredScopes: ["workspace:read"] }));

app.post("/mcp", async (req, res) => {
  const server = new McpServer({ name: "workspace-hosted", version: "1.2.0" });
  registerGitTools(server);
  registerSearchTools(server);
  const transport = new NodeStreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});

app.listen(8443, "0.0.0.0");
