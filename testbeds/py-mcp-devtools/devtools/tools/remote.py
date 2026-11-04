"""Health checks on the ops hosts over SSH."""

from typing import Literal

import paramiko

from devtools.app import mcp
from devtools.settings import settings

CHECKS = {
    "uptime": "uptime",
    "disk": "df -h /",
    "memory": "free -m",
}


class RemoteHost:
    def __init__(self, hostname: str):
        if hostname not in settings.ssh_hosts:
            raise ValueError(f"unknown host {hostname!r}")
        self.hostname = hostname
        self._client = paramiko.SSHClient()
        self._client.load_system_host_keys()

    def run(self, command: str) -> str:
        self._client.connect(self.hostname, username=settings.ssh_user, timeout=10)
        try:
            _, stdout, stderr = self._client.exec_command(command, timeout=20)
            return stdout.read().decode() + stderr.read().decode()
        finally:
            self._client.close()


@mcp.tool()
def host_check(hostname: str, check: Literal["uptime", "disk", "memory"] = "uptime") -> str:
    """Run one of the standard health checks on an ops host."""
    return RemoteHost(hostname).run(CHECKS[check])


@mcp.tool()
def host_journal(hostname: str, unit: str, lines: int = 50) -> str:
    """Recent journal lines for a unit on an ops host."""
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(hostname, username=settings.ssh_user, timeout=10)
    _, stdout, _ = client.exec_command(f"journalctl -u {unit} -n {lines} --no-pager")
    return stdout.read().decode()
