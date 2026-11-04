import os

# os.putenv changes the C environment only; os.environ (which fastmcp's settings read) keeps
# its old value.
os.putenv("FASTMCP_HOST", "0.0.0.0")

from fastmcp import FastMCP  # noqa: E402

metrics = FastMCP("metrics")

if __name__ == "__main__":
    # ok: mcp-server-exposed-without-auth
    metrics.run(transport="http")
