# fastmcp's protection switched on for the whole process.
import fastmcp
from fastmcp import FastMCP

fastmcp.settings.http_host_origin_protection = "auto"

docs = FastMCP("docs")
# ok: mcp-http-transport-without-host-validation
docs.run(transport="http")
