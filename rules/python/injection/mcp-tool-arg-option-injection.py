import asyncio
import re
import subprocess
from pathlib import Path

from git import Repo
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("git-tools")
REPO = Repo("/srv/checkout")


@mcp.tool()
def git_diff(target: str) -> str:
    # ruleid: mcp-tool-arg-option-injection
    return REPO.git.diff("--unified=3", target)


@mcp.tool()
def git_checkout(branch_name: str) -> str:
    # ruleid: mcp-tool-arg-option-injection
    REPO.git.checkout(branch_name)
    return f"Switched to {branch_name}"


@mcp.tool()
def git_log(ref: str) -> str:
    # ruleid: mcp-tool-arg-option-injection
    return subprocess.run(["git", "log", "--oneline", ref], capture_output=True, text=True).stdout


@mcp.tool()
def compare(base: str) -> str:
    # ruleid: mcp-tool-arg-option-injection
    return subprocess.check_output(["git", "diff", "--stat", f"{base}...HEAD"], text=True)


@mcp.tool()
async def fetch(remote: str, branch: str) -> str:
    # ruleid: mcp-tool-arg-option-injection
    proc = await asyncio.create_subprocess_exec("git", "fetch", "origin", branch)
    await proc.wait()
    return "fetched"


@mcp.tool()
def search_code(pattern: str) -> str:
    # ruleid: mcp-tool-arg-option-injection
    argv = ["rg", "--json", pattern, "/srv/checkout"]
    return subprocess.run(argv, capture_output=True, text=True).stdout


@mcp.tool()
def download(url: str) -> str:
    # ruleid: mcp-tool-arg-option-injection
    subprocess.run(("curl", "-fsSL", "--retry", "2", url), check=True)
    return "ok"


# --- Near misses ---


@mcp.tool()
def git_diff_safe(target: str) -> str:
    # ok: mcp-tool-arg-option-injection
    return REPO.git.diff("--unified=3", "--", target)


@mcp.tool()
def git_checkout_checked(branch_name: str) -> str:
    if branch_name.startswith("-"):
        raise ValueError(f"Invalid branch name: {branch_name!r}")
    # ok: mcp-tool-arg-option-injection
    REPO.git.checkout(branch_name)
    return f"Switched to {branch_name}"


@mcp.tool()
def git_show(sha: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{7,40}", sha):
        raise ValueError("expected a commit SHA")
    # ok: mcp-tool-arg-option-injection
    return subprocess.check_output(["git", "show", "--stat", sha], text=True)


@mcp.tool()
def commit(message: str) -> str:
    # ok: mcp-tool-arg-option-injection
    return subprocess.check_output(["git", "commit", "-m", message], text=True)


@mcp.tool()
def log_upstream(branch: str) -> str:
    # ok: mcp-tool-arg-option-injection
    return subprocess.check_output(["git", "log", "--oneline", f"origin/{branch}"], text=True)


@mcp.tool()
def search_safe(pattern: str) -> str:
    # ok: mcp-tool-arg-option-injection
    return subprocess.run(["rg", "--json", "-e", pattern, "--", "/srv/checkout"], capture_output=True).stdout


@mcp.tool()
def list_files(folder: str) -> str:
    # ok: mcp-tool-arg-option-injection
    return subprocess.check_output(["ls", "-la", folder], text=True)


@mcp.tool()
def git_log_end_of_options(ref: str) -> str:
    # ok: mcp-tool-arg-option-injection
    return subprocess.check_output(["git", "log", "--oneline", "--end-of-options", ref], text=True)


@mcp.tool()
def git_log_since(repo_path: str, since: str | None = None) -> list[str]:
    repo = Repo(repo_path)
    args = []
    if since:
        args.extend(["--since", since])
    # ok: mcp-tool-arg-option-injection
    return repo.git.log(*args, "--format=%H %s").splitlines()


@mcp.tool()
def commit_and_restore(repo_path: str, message: str) -> str:
    repo = Repo(repo_path)
    repo.index.commit(message)
    stash_oid = (Path(repo.git_dir) / "MERGE_AUTOSTASH").read_text().strip()
    # ok: mcp-tool-arg-option-injection
    repo.git.stash("apply", stash_oid)
    return "applied"
