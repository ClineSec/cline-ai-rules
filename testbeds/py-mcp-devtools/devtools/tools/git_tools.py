"""Git history and diffs for the repository checkout."""

import re
import subprocess
from typing import Literal

from git import Repo
from git.exc import BadName

from devtools.app import REPO_ROOT, mcp

_repo = Repo(REPO_ROOT)

SHA_RE = re.compile(r"[0-9a-f]{7,40}")
MAX_DIFF_CHARS = 40_000


def _clip(text: str) -> str:
    if len(text) > MAX_DIFF_CHARS:
        return text[:MAX_DIFF_CHARS] + "\n... (truncated)"
    return text


@mcp.tool()
def git_status() -> str:
    """Short status of the working tree."""
    return _repo.git.status("--short", "--branch")


@mcp.tool()
def git_diff(target: str, context_lines: int = 3) -> str:
    """Diff the working tree against a branch, tag, or commit."""
    return _clip(_repo.git.diff(f"--unified={context_lines}", target))


@mcp.tool()
def git_diff_paths(target: str, paths: list[str]) -> str:
    """Diff selected paths against a revision."""
    try:
        _repo.rev_parse(target)
    except BadName:
        return f"Unknown revision: {target}"
    return _clip(_repo.git.diff(target, "--", *paths))


@mcp.tool()
def git_log(ref: str = "HEAD", max_count: int = 20) -> str:
    """One-line history for a ref."""
    argv = ["git", "-C", str(REPO_ROOT), "log", "--oneline", f"--max-count={max_count}", ref]
    return subprocess.run(argv, capture_output=True, text=True, check=False).stdout


@mcp.tool()
def git_show(sha: str, stat_only: bool = True) -> str:
    """Show a commit by SHA."""
    if not SHA_RE.fullmatch(sha):
        return "Expected a commit SHA (7-40 hex characters)."
    args = ["--stat"] if stat_only else []
    return _clip(_repo.git.show(*args, sha))


@mcp.tool()
def git_branches(scope: Literal["local", "remote", "all"] = "local") -> str:
    """List branches."""
    flag = {"local": "--list", "remote": "--remotes", "all": "--all"}[scope]
    return _repo.git.branch(flag, "--format=%(refname:short)")


@mcp.tool()
def git_checkout(branch: str) -> str:
    """Switch the checkout to an existing branch."""
    if branch.startswith("-"):
        return f"Refusing branch name that looks like an option: {branch}"
    _repo.git.checkout(branch)
    return f"Switched to {branch}"


@mcp.tool()
def git_blame(path: str, start: int, end: int) -> str:
    """Blame a line range of a file."""
    return _repo.git.blame("-L", f"{start},{end}", "--", path)
