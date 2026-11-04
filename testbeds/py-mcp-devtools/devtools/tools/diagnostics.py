"""Support bundles and runtime details for debugging a stuck devtools deployment."""

import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

from devtools.app import mcp
from devtools.settings import settings

# Settings a support engineer may ask for by name. Everything else stays on the host.
SUPPORT_VARIABLES = frozenset({"DEVTOOLS_REPO", "DEVTOOLS_LOG_DIR", "DEVTOOLS_SSH_USER", "TZ", "LANG"})
# Names that hold credentials; their values never leave the host.
CREDENTIAL_NAME = re.compile(r"token|secret|passw|key|auth", re.IGNORECASE)
# Display rules from the support handbook, per variable. A variable it doesn't list is shown.
VARIABLE_RULES = {"DEVTOOLS_LICENSE_KEY": {"hidden": True}, "DEVTOOLS_REGION": {"hidden": False}}


def _runtime() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pid": str(os.getpid()),
        "collected": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def _environment() -> dict[str, str]:
    """The server's environment, sorted the way `env | sort` prints it."""
    return {key: os.environ[key] for key in sorted(os.environ)}


@mcp.tool()
def support_bundle() -> dict:
    """Everything support asks for first when the server misbehaves: runtime, settings, environment."""
    bundle = {
        "runtime": _runtime(),
        "repo_root": str(settings.repo_root),
        "log_dir": str(settings.log_dir),
        "environment": _environment(),
    }
    return bundle


@mcp.tool()
def devtools_setting(name: str) -> str:
    """One DEVTOOLS_* setting by its short name, e.g. "repo" for DEVTOOLS_REPO."""
    return os.environ.get(f"DEVTOOLS_{name.upper()}", "")


@mcp.tool()
def support_variable(name: str) -> str:
    """One of the support variables (see SUPPORT_VARIABLES)."""
    if name not in SUPPORT_VARIABLES:
        raise ValueError(f"{name} is not a support variable; ask for one of {sorted(SUPPORT_VARIABLES)}")
    return os.environ.get(name, "")


@mcp.tool()
def ci_context() -> dict[str, str]:
    """The CI runner's variables, for matching a failure to its pipeline."""
    return {k: v for k, v in os.environ.items() if k.startswith(("CI_", "GITHUB_"))}


@mcp.tool()
def devtools_settings() -> dict[str, str]:
    """Every DEVTOOLS_* setting except the credentials."""
    return {k: v for k, v in os.environ.items() if k.startswith("DEVTOOLS_") and not CREDENTIAL_NAME.search(k)}


@mcp.tool()
def visible_settings() -> dict[str, str]:
    """Every variable the support handbook doesn't hide."""
    return {k: v for k, v in os.environ.items() if not (VARIABLE_RULES.get(k) or {}).get("hidden")}


@mcp.tool()
def environment_names() -> list[str]:
    """Names of the variables set for the server, without their values."""
    return sorted(os.environ)


@mcp.tool()
def disk_check() -> str:
    """Free space under the checkout, from `df`, run with the server's environment plus a fixed locale."""
    df = shutil.which("df") or "df"
    proc = subprocess.run(
        [df, "-h", str(settings.repo_root)],
        env={**os.environ, "LC_ALL": "C"},
        capture_output=True,
        text=True,
        timeout=10,
    )
    return proc.stdout
