"""The shared-cluster deployment: the same tools behind the company's OAuth server.

Every request carries a bearer token that the cluster's identity provider issued for this
server; ClusterTokenVerifier checks it against the provider's introspection endpoint.
"""

import os

import httpx
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer

ISSUER = os.environ.get("DEVTOOLS_ISSUER", "https://auth.example.com")
RESOURCE = os.environ.get("DEVTOOLS_RESOURCE", "https://devtools.example.com/mcp")


class ClusterTokenVerifier:
    async def verify_token(self, token: str) -> AccessToken | None:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(f"{ISSUER}/oauth/introspect", data={"token": token})
        claims = resp.json()
        if not claims.get("active") or claims.get("aud") != RESOURCE:
            return None
        return AccessToken(token=token, client_id=claims["client_id"], scopes=claims.get("scope", "").split())


hosted = MCPServer(
    "devtools-hosted",
    token_verifier=ClusterTokenVerifier(),
    auth=AuthSettings(issuer_url=ISSUER, resource_server_url=RESOURCE, required_scopes=["devtools:read"]),
)


if __name__ == "__main__":
    hosted.run("streamable-http", host="0.0.0.0", port=8443)
