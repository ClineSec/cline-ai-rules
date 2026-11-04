"""Coverage reports for the coding agents (standalone fastmcp).

Shares the build VM with build_status_server.py, but the coverage data includes unreleased
module names, so every request needs a token from the team's identity provider.
"""

import os

os.environ.setdefault("FASTMCP_HOST", "0.0.0.0")
os.environ.setdefault("FASTMCP_PORT", "8045")

from fastmcp import FastMCP  # noqa: E402
from fastmcp.server.auth.providers.jwt import JWTVerifier  # noqa: E402

verifier = JWTVerifier(
    jwks_uri="https://idp.example.com/.well-known/jwks.json",
    issuer="https://idp.example.com/",
    audience="devtools-coverage",
)
coverage = FastMCP("coverage", auth=verifier)


@coverage.tool
def module_coverage(module: str) -> dict[str, float]:
    """Line and branch coverage of one module from the last main build."""
    return {"module": module, "lines": 0.0, "branches": 0.0}


if __name__ == "__main__":
    coverage.run(transport="http")
