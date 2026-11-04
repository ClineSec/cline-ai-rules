import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    repo_root: Path = field(default_factory=lambda: Path(os.environ.get("DEVTOOLS_REPO", "/srv/checkout")))
    ssh_user: str = os.environ.get("DEVTOOLS_SSH_USER", "deploy")
    ssh_hosts: tuple[str, ...] = ("web-1.example.com", "web-2.example.com", "worker-1.example.com")
    log_dir: Path = Path(os.environ.get("DEVTOOLS_LOG_DIR", "/var/log/app"))


settings = Settings()
