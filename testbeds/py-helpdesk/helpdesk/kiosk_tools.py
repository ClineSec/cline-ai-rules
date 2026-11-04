"""LangChain tools for the lobby kiosk agent (print queues and kiosk health)."""

import subprocess

from langchain_core.tools import tool


@tool
def kiosk_queue(printer: str) -> str:
    """Show the jobs waiting on one lobby printer."""
    return subprocess.check_output(args=f"lpq -P {printer}", shell=True, text=True, timeout=10)


@tool
def kiosk_uptime(kiosk: str) -> str:
    """Show how long a lobby kiosk has been up."""
    return subprocess.check_output(args=["ssh", "--", f"kiosk@{kiosk}.lobby.example.com", "uptime"], text=True, timeout=10)
