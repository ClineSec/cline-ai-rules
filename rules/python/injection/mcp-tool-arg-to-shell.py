import asyncio
import os
import re
import shlex
import subprocess
from typing import Annotated, Literal

import anyio
import mcp.types as types
import paramiko
from mcp.server.lowlevel import Server
from mcp.server.mcpserver import Context, MCPServer
from pydantic import Field

mcp = MCPServer("devbox")


@mcp.tool()
def git_log(branch: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.check_output(f"git log --oneline {branch}", shell=True, text=True)


@mcp.tool(name="disk_usage", description="Show disk usage for a folder")
async def disk_usage(folder: str, ctx: Context) -> str:
    cmd = "du -sh " + folder
    # ruleid: mcp-tool-arg-to-shell
    proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE)
    out, _ = await proc.communicate()
    return out.decode()


@mcp.tool()
def grep_logs(pattern: str, path: str = "/var/log/app.log") -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.getoutput("grep -n '%s' %s" % (pattern, path))


@mcp.tool()
def ping(host):
    # ruleid: mcp-tool-arg-to-shell
    return os.system("ping -c 1 " + host)


@mcp.tool()
def calc(expression: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return str(eval(expression))


@mcp.tool()
def run_script(command: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.run(["bash", "-lc", command], capture_output=True, text=True).stdout


@mcp.tool()
def run_in_container(container: str, command: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    argv = ["docker", "exec", container, "sh", "-c", command]
    return subprocess.run(argv, capture_output=True, text=True).stdout


@mcp.tool()
async def tail(path: str, lines: int = 50) -> str:
    cmd = f"tail -n {lines} {path}"
    # ruleid: mcp-tool-arg-to-shell
    result = await anyio.run_process(cmd)
    return result.stdout.decode()


@mcp.tool()
def remote_uptime(host: str, unit: str) -> str:
    client = paramiko.SSHClient()
    client.connect(host)
    # ruleid: mcp-tool-arg-to-shell
    _, stdout, _ = client.exec_command(f"systemctl status {unit}")
    return stdout.read().decode()


def list_dir(path: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return os.popen("ls -la " + path).read()


mcp.add_tool(list_dir)


async def call_tool(ctx, params: types.CallToolRequestParams) -> types.CallToolResult:
    service = params.arguments["service"]
    # ruleid: mcp-tool-arg-to-shell
    out = subprocess.run(f"journalctl -u {service} -n 20", shell=True, capture_output=True)
    return types.CallToolResult(content=[types.TextContent(text=out.stdout.decode())])


async def handle_tool(ctx, params):
    # ruleid: mcp-tool-arg-to-shell
    os.system("make " + params.arguments["target"])


lowlevel = Server("builder", on_call_tool=handle_tool)


# --- Near misses ---


@mcp.tool()
def git_log_safe(branch: str) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.check_output(["git", "log", "--oneline", "--", branch], text=True)


@mcp.tool()
def git_log_quoted(branch: str) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.check_output(f"git log --oneline {shlex.quote(branch)}", shell=True, text=True)


@mcp.tool()
def status() -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.check_output("git status --short", shell=True, text=True)


@mcp.tool()
def recent(count: int, fmt: Literal["short", "full"] = "short") -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.check_output(f"git log -n {count} --format={fmt}", shell=True, text=True)


LogFormat = Literal["short", "full", "oneline"]
Ref = str


@mcp.tool()
def recent_as(fmt: LogFormat, count: int = 5) -> str:
    # A Literal alias is as safe as the Literal written inline.
    # ok: mcp-tool-arg-to-shell
    return subprocess.check_output(f"git log -n {count} --format={fmt}", shell=True, text=True)


@mcp.tool()
def show_ref(ref: Ref) -> str:
    # An alias of str is still free text.
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.check_output(f"git show {ref}", shell=True, text=True)


@mcp.tool()
def top(limit: Annotated[int, Field(ge=1, le=50)] = 10) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.getoutput(f"ps aux --sort=-%cpu | head -n {limit}")


@mcp.tool()
async def tail_argv(path: str) -> str:
    # ok: mcp-tool-arg-to-shell
    result = await anyio.run_process(["tail", "-n", "50", path])
    return result.stdout.decode()


@mcp.tool()
def env_only(note: str) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.check_output("printenv NOTE", shell=True, env={"NOTE": note}, text=True)


@mcp.tool()
def bash_script(name: str) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.run(["bash", "-c", 'echo "hello, $1"', "greeter", name], capture_output=True).stdout


def not_a_tool(path: str) -> str:
    # ok: mcp-tool-arg-to-shell
    return os.popen("ls -la " + path).read()


@mcp.tool()
def checkout(branch: Annotated[str, Field(pattern=r"^[A-Za-z0-9._/-]+$")]) -> str:
    # ok: mcp-tool-arg-to-shell
    return subprocess.check_output(f"git checkout {branch}", shell=True, text=True)


@mcp.tool()
def show(ref: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{7,40}", ref):
        raise ValueError("ref must be a commit SHA")
    # ok: mcp-tool-arg-to-shell
    return subprocess.check_output(f"git show --stat {ref}", shell=True, text=True)


@mcp.tool()
def show_loose(ref: str) -> str:
    if not re.match(r"[0-9a-f]+", ref):
        raise ValueError("ref must be a commit SHA")
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.check_output(f"git show --stat {ref}", shell=True, text=True)


@mcp.tool()
def ratio(formula: str, values: list[float]) -> float:
    # ruleid: mcp-tool-arg-to-shell
    return float(eval(formula, {"__builtins__": {}}, {"x": values}))


ALLOWED_UNITS = {"nginx", "app-web"}


@mcp.tool()
def unit_status(unit: str) -> str:
    if unit not in ALLOWED_UNITS:
        raise ValueError(f"unknown unit {unit!r}")
    # ok: mcp-tool-arg-to-shell
    return subprocess.getoutput(f"systemctl status {unit}")


@mcp.tool()
def unit_status_blocklist(unit: str) -> str:
    if ";" in unit:
        raise ValueError("no semicolons")
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.getoutput(f"systemctl status {unit}")


# --- The command passed by keyword ------------------------------------------------------

@mcp.tool()
def journal(service: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    out = subprocess.run(args=f"journalctl -u {service} -n 20", shell=True, capture_output=True)
    return out.stdout.decode()


@mcp.tool()
def journal_argv(service: str) -> str:
    # With shell=True the later list items are the shell's $0, $1, ..., not commands.
    # ok: mcp-tool-arg-to-shell
    out = subprocess.run(shell=True, args=["journalctl -u \"$1\" -n 20", "journal", service])
    return out.stdout.decode()


@mcp.tool()
def make_target(target: str) -> int:
    # ruleid: mcp-tool-arg-to-shell
    return os.system(command="make " + target)


@mcp.tool()
def grep_keyword(pattern: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return subprocess.getoutput(cmd=f"grep -rn {pattern} docs/")


@mcp.tool()
def disk_free(mount: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    return os.popen(cmd=f"df -h {mount}").read()


@mcp.tool()
async def du_keyword(folder: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    proc = await asyncio.create_subprocess_shell(cmd=f"du -sh {folder}", stdout=asyncio.subprocess.PIPE)
    out, _ = await proc.communicate()
    return out.decode()


@mcp.tool()
async def note_keyword(note: str) -> str:
    # ok: mcp-tool-arg-to-shell
    proc = await asyncio.create_subprocess_shell(cmd="printenv NOTE", env={"NOTE": note}, stdout=asyncio.subprocess.PIPE)
    out, _ = await proc.communicate()
    return out.decode()


@mcp.tool()
def remote_status(host: str, unit: str) -> str:
    client = paramiko.SSHClient()
    client.connect(host)
    # ruleid: mcp-tool-arg-to-shell
    _, stdout, _ = client.exec_command(command=f"systemctl status {unit}", timeout=10)
    return stdout.read().decode()


@mcp.tool()
async def tail_keyword(path: str) -> str:
    # ruleid: mcp-tool-arg-to-shell
    result = await anyio.run_process(command=f"tail -n 50 {path}")
    # ok: mcp-tool-arg-to-shell
    listing = await anyio.run_process(command=["tail", "-n", "50", "--", path])
    return result.stdout.decode() + listing.stdout.decode()
