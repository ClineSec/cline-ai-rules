import os

from dotenv import dotenv_values
from fastmcp import FastMCP
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("env-resources")
fm = FastMCP("env-prompts")

PROCESS_ENV = os.environ.copy()
MERGED_ENV = {**os.environ, "APP_MODE": "diagnostics"}
DOTENV_SETTINGS = dotenv_values(".env")
DEFAULTS = {"TZ": "UTC", "LANG": "C.UTF-8"}


@mcp.resource("env://all")
def all_env() -> dict[str, str]:
    # ruleid: mcp-tool-returns-environment
    return dict(os.environ)


@fm.prompt
def debug_prompt() -> str:
    # ruleid: mcp-tool-returns-environment
    return f"Debug this environment: {dict(os.environ)}"


def env_template(name: str) -> str:
    # ruleid: mcp-tool-returns-environment
    return str(os.environ)


fm.add_prompt(env_template)


@mcp.resource("env://snapshot")
def snapshot() -> dict[str, str]:
    # ruleid: mcp-tool-returns-environment
    return PROCESS_ENV


@fm.prompt
def merged_prompt() -> str:
    # ruleid: mcp-tool-returns-environment
    return f"Settings: {MERGED_ENV}"


@mcp.resource("env://dotenv")
def dotenv_resource() -> dict:
    # ruleid: mcp-tool-returns-environment
    return dict(DOTENV_SETTINGS)


@mcp.resource("env://defaults")
def defaults() -> dict[str, str]:
    # ok: mcp-tool-returns-environment
    return DEFAULTS


@mcp.resource("env://{name}")
def one_var(name: str) -> str:
    # ok: mcp-tool-returns-environment
    return os.environ.get("APP_REGION", "")


def helper() -> dict:
    # ok: mcp-tool-returns-environment
    return dict(os.environ)
