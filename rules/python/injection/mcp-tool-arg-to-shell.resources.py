# Resource templates and prompts: the client fills a template's URI variables and a prompt's
# arguments, and clients let the model choose them, so they're sources like tool arguments.
import subprocess
from typing import Literal, TypeAlias

import mcp.types as types
from dagster import resource
from fastmcp import FastMCP
from fastmcp.prompts import prompt
from fastmcp.resources import ResourceTemplate
from fastmcp.resources import resource as fm_resource
from mcp.server import Server as LegacyServer
from mcp.server.lowlevel import Server
from mcp.server.mcpserver import MCPServer
from mcp.types import GetPromptRequestParams, ReadResourceRequestParams
from pydantic import AnyUrl

mcp = MCPServer("logs")
fm = FastMCP("runbooks")
legacy = LegacyServer("legacy-logs")


@mcp.resource("logs://{service}/tail")
def tail_logs(service: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.getoutput(f"journalctl -u {service} -n 50")


@mcp.prompt()
def triage(service: str, since: str = "1h") -> str:
    # ruleid: mcp-tool-arg-to-shell
    status = subprocess.check_output("systemctl status " + service, shell=True, text=True)
    return f"Triage {service} since {since}:\n{status}"


@fm.prompt
def explain_unit(unit: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.getoutput("systemctl cat " + unit)


@fm_resource("runbook://{name}")
def runbook(name: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.run(f"cat /srv/runbooks/{name}.md", shell=True, capture_output=True, text=True).stdout


@prompt
def disk_report(mount: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.getoutput(f"df -h {mount}")


def unit_env(unit: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.getoutput(f"systemctl show {unit} -p Environment")


def unit_deps(unit: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.getoutput(f"systemctl list-dependencies {unit}")


fm.add_prompt(unit_env)
fm.add_template(ResourceTemplate.from_function(unit_deps, uri_template="deps://{unit}"))


@legacy.read_resource()
async def read_legacy(uri: AnyUrl) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.getoutput(f"curl -s {uri}")


@legacy.get_prompt()
async def get_legacy_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
    unit = (arguments or {}).get("unit", "")
    # ruleid: mcp-tool-arg-to-shell
    status = subprocess.getoutput("systemctl is-active " + unit)
    return types.GetPromptResult(messages=[])


async def on_read(ctx, params: ReadResourceRequestParams):
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.getoutput(f"cat {params.uri}")


async def on_prompt(ctx, params):
    # ruleid: mcp-tool-arg-to-shell
    out = subprocess.getoutput("journalctl -u " + params.arguments["unit"])
    return out


async def on_prompt_typed(ctx, params: GetPromptRequestParams):
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.getoutput("systemctl status " + params.arguments["unit"])


low = Server("logs-low", on_read_resource=on_read, on_get_prompt=on_prompt)


# --- Near misses ---


@mcp.resource("logs://system/summary")
def system_summary() -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.getoutput("journalctl -n 20")


@mcp.resource("logs://{service}/safe")
def tail_logs_safe(service: str) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.run(["journalctl", "-u", service, "-n", "50"], capture_output=True, text=True).stdout


@mcp.prompt()
def level_report(level: Literal["info", "warning", "error"], limit: int) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.getoutput(f"journalctl -p {level} -n {limit}")


Severity: TypeAlias = Literal["info", "warning", "error"]


@mcp.resource("logs://severity/{severity}")
def severity_log(severity: Severity) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.getoutput(f"journalctl -p {severity} -n 50")


@resource(config_schema={"host": str})
def ssh_tunnel(init_context):
    # Dagster's @resource builds a pipeline resource from run config, not an MCP resource.
    # ok: mcp-tool-arg-to-shell
    return subprocess.Popen("ssh -N " + init_context.resource_config["host"], shell=True)


def not_registered(unit: str) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.getoutput(f"systemctl status {unit}")

