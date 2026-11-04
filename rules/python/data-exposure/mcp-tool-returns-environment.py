import base64
import json
import os
import re
import subprocess
from pathlib import Path

import mcp.types as types
import psutil
from dotenv import dotenv_values
from mcp.server.fastmcp import FastMCP as LegacyFastMCP
from mcp.server.lowlevel import Server
from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

mcp = MCPServer("diagnostics")
legacy = LegacyFastMCP("diagnostics-legacy")


class EnvReport(BaseModel):
    variables: dict[str, str]
    cwd: str


@mcp.tool()
def environment() -> dict[str, str]:
    """Environment variables of the server process."""
    # ruleid: mcp-tool-returns-environment
    return dict(os.environ)


@mcp.tool
def environment_bare():
    # ruleid: mcp-tool-returns-environment
    return os.environ


@legacy.tool()
def environment_json() -> str:
    # ruleid: mcp-tool-returns-environment
    return json.dumps({**os.environ, "SERVER": "legacy"}, indent=2)


@mcp.tool()
async def environment_lines() -> str:
    # ruleid: mcp-tool-returns-environment
    return "\n".join(f"{k}={v}" for k, v in sorted(os.environ.items()))


@mcp.tool()
def merged_environment(overrides: dict[str, str]) -> dict[str, str]:
    env = os.environ.copy()
    env.update(overrides)
    # ruleid: mcp-tool-returns-environment
    return env


@mcp.tool()
def environment_report() -> EnvReport:
    # ruleid: mcp-tool-returns-environment
    return EnvReport(variables=dict(os.environ), cwd=os.getcwd())


@mcp.tool()
def printenv() -> str:
    proc = subprocess.run(["printenv"], capture_output=True, text=True, check=False)
    # ruleid: mcp-tool-returns-environment
    return proc.stdout


@mcp.tool()
def dotenv_settings() -> dict:
    # ruleid: mcp-tool-returns-environment
    return {"file": ".env", "values": dotenv_values(".env")}


@mcp.tool()
def process_environment(pid: int) -> str:
    # ruleid: mcp-tool-returns-environment
    return Path(f"/proc/{pid}/environ").read_text().replace("\0", "\n")


@mcp.tool()
def worker_environment(pid: int) -> dict:
    proc = psutil.Process(pid)
    # ruleid: mcp-tool-returns-environment
    return {"pid": pid, "environ": proc.environ()}


@mcp.tool()
def github_auth() -> dict:
    # ruleid: mcp-tool-returns-environment
    return {"user": os.environ.get("GITHUB_USER", ""), "token": os.environ.get("GITHUB_TOKEN", "")}


@mcp.tool()
def model_key() -> str:
    key = os.getenv("OPENAI_API_KEY")
    # ruleid: mcp-tool-returns-environment
    return f"Using key {key}"


def runtime_info() -> list[str]:
    # ruleid: mcp-tool-returns-environment
    return [f"{k}={v}" for k, v in os.environ.items()]


mcp.add_tool(runtime_info)


@mcp.tool()
def environment_by_name() -> dict[str, str]:
    # ruleid: mcp-tool-returns-environment
    return {key: os.environ[key] for key in sorted(os.environ)}


@mcp.tool()
def read_variable(name: str) -> str:
    """Value of one environment variable."""
    # ruleid: mcp-tool-returns-environment
    return os.environ.get(name, "")


STARTUP_ENV = dict(os.environ)


@mcp.tool()
def startup_environment() -> dict[str, str]:
    # ruleid: mcp-tool-returns-environment
    return STARTUP_ENV


server = Server("diagnostics-lowlevel")


@server.call_tool()
async def handle_call(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "env":
        # ruleid: mcp-tool-returns-environment
        return [types.TextContent(type="text", text=json.dumps(dict(os.environ)))]
    if name == "getenv":
        value = os.environ[arguments["variable"]]
        # ruleid: mcp-tool-returns-environment
        return [types.TextContent(type="text", text=value)]
    return [types.TextContent(type="text", text="unknown tool")]


async def on_call_tool(ctx, params: types.CallToolRequestParams) -> types.CallToolResult:
    snapshot = str(os.environ)
    # ruleid: mcp-tool-returns-environment
    return types.CallToolResult(content=[types.TextContent(text=snapshot)])


v2_server = Server("diagnostics-v2", on_call_tool=on_call_tool)


# A prefix is not an allowlist: GITHUB_ keeps GITHUB_TOKEN, and masking AWS_ leaves the rest.
@mcp.tool()
def github_settings() -> dict[str, str]:
    # ruleid: mcp-tool-returns-environment
    return {k: v for k, v in os.environ.items() if k.startswith("GITHUB_")}


@mcp.tool()
def ci_variables() -> list[str]:
    # ruleid: mcp-tool-returns-environment
    return [f"{k}={os.environ[k]}" for k in sorted(os.environ) if k.startswith(("CI_", "BUILD_"))]


@mcp.tool()
def masked_environment() -> dict[str, str]:
    # ruleid: mcp-tool-returns-environment
    return {k: "***" if k.startswith("AWS_") else v for k, v in os.environ.items()}


@mcp.tool()
def app_environment() -> dict[str, str]:
    # ruleid: mcp-tool-returns-environment
    return dict(filter(lambda item: item[0].startswith("APP_"), os.environ.items()))


# A policy table hides only the variables it lists; every other one, secrets included, is
# returned. The condition starts with a parenthesized expression and a method call, which made
# OpenGrep 1.30.2 drop every finding in this file ("Invalid_argument: String.sub") before the
# filter sanitizers skipped such conditions.
VARIABLE_POLICY = {"DIAG_REGION": {"hidden": False}, "DIAG_DEBUG_DUMP": {"hidden": True}}


@mcp.tool()
def policy_settings() -> dict[str, str]:
    # ruleid: mcp-tool-returns-environment
    return {k: v for k, v in os.environ.items() if not (VARIABLE_POLICY.get(k) or {}).get("hidden")}


@mcp.tool()
def encoded_environment() -> str:
    # ruleid: mcp-tool-returns-environment
    return base64.b64encode(json.dumps(dict(os.environ)).encode()).decode()


# Near misses: named, non-secret settings, facts about secrets, and the environment handed to
# a process rather than returned.

@mcp.tool()
def timezone() -> dict[str, str]:
    env = dict(os.environ)
    # ok: mcp-tool-returns-environment
    return {"tz": env["TZ"], "lang": os.environ.get("LANG", "C.UTF-8"), "home": os.environ["HOME"]}


@mcp.tool()
def credentials_status() -> dict[str, bool]:
    # ok: mcp-tool-returns-environment
    return {"github": "GITHUB_TOKEN" in os.environ, "openai": bool(os.getenv("OPENAI_API_KEY"))}


@mcp.tool()
def variable_names() -> list[str]:
    # ok: mcp-tool-returns-environment
    return sorted(os.environ)


@mcp.tool()
def variable_count() -> int:
    # ok: mcp-tool-returns-environment
    return len(os.environ)


LOCALE_VARIABLES = ("LANG", "LC_ALL", "TZ")


@mcp.tool()
def locale_variables() -> dict[str, str | None]:
    # ok: mcp-tool-returns-environment
    return {key: os.environ.get(key) for key in LOCALE_VARIABLES}


@mcp.tool()
def value_lengths() -> list[int]:
    # ok: mcp-tool-returns-environment
    return [len(value) for value in os.environ.values()]


@mcp.tool()
def token_preview() -> str:
    token = os.environ.get("GITHUB_TOKEN", "")
    # ok: mcp-tool-returns-environment
    return token[:4] + "..." if token else "not set"


@mcp.tool()
def git_status() -> str:
    env = {**os.environ, "GIT_PAGER": "cat"}
    proc = subprocess.run(["git", "status", "--short"], env=env, capture_output=True, text=True)
    # ok: mcp-tool-returns-environment
    return proc.stdout


@mcp.tool()
def redacted_environment() -> dict[str, str]:
    # ok: mcp-tool-returns-environment
    return {k: "***" if "KEY" in k or "TOKEN" in k else v for k, v in os.environ.items()}


@mcp.tool()
def home_directory() -> str:
    # ok: mcp-tool-returns-environment
    return subprocess.run(["printenv", "HOME"], capture_output=True, text=True).stdout


SHOWN_VARIABLES = {"TZ", "LANG", "DIAG_REGION"}
SECRET_NAME = re.compile(r"token|secret|passw|key|auth", re.IGNORECASE)


@mcp.tool()
def shown_settings() -> dict[str, str]:
    # ok: mcp-tool-returns-environment
    return {k: v for k, v in os.environ.items() if k in SHOWN_VARIABLES}


@mcp.tool()
def diag_settings() -> str:
    # ok: mcp-tool-returns-environment
    return json.dumps({k: v for k, v in os.environ.items() if k.startswith("DIAG_") and not SECRET_NAME.search(k)})


@mcp.tool()
def public_settings() -> dict[str, str]:
    # ok: mcp-tool-returns-environment
    return {k: v for k, v in os.environ.items() if "TOKEN" not in k and "SECRET" not in k and "KEY" not in k}


@mcp.tool()
def safe_environment() -> dict[str, str]:
    # ok: mcp-tool-returns-environment
    return {k: "***" if SECRET_NAME.search(k) else v for k, v in os.environ.items()}


@mcp.tool()
def shown_entries() -> dict[str, str]:
    # ok: mcp-tool-returns-environment
    return dict(filter(lambda item: item[0] in SHOWN_VARIABLES, os.environ.items()))


@mcp.tool()
def read_allowed_variable(name: str) -> str:
    if name not in SHOWN_VARIABLES:
        raise ValueError(f"{name} is not one of {sorted(SHOWN_VARIABLES)}")
    # ok: mcp-tool-returns-environment
    return os.environ.get(name, "")


@mcp.tool()
def echo_name(name: str) -> dict[str, str]:
    # ok: mcp-tool-returns-environment
    return {"name": name, "region": STARTUP_ENV["DIAG_REGION"]}


@mcp.tool()
def health() -> str:
    # ok: mcp-tool-returns-environment
    return json.dumps({"ok": True, "pid": os.getpid()})


def debug_dump() -> dict[str, str]:
    """Not registered as a tool: called from the CLI only."""
    # ok: mcp-tool-returns-environment
    return dict(os.environ)
