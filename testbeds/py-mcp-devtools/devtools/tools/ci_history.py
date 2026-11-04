"""CI run history, read from the build bot's SQLite database.

The build bot writes one row per job run; these tools let the agent ask which jobs failed on a
branch and how long builds take, without shelling into the bot.
"""

import sqlite3
from contextlib import closing
from typing import Literal

from devtools.app import mcp
from devtools.settings import settings

RUNS_DB = settings.repo_root / ".ci" / "runs.sqlite"


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{RUNS_DB}?mode=ro", uri=True)


@mcp.tool()
def failed_runs(branch: str, job: str | None = None, since: str | None = None) -> list[dict]:
    """Failed CI runs on a branch, newest first. `since` is an ISO date."""
    clauses = [f"branch = '{branch}'", "status = 'failed'"]
    if job:
        clauses.append(f"job = '{job}'")
    if since:
        clauses.append(f"started_at >= '{since}'")
    query = "SELECT job, started_at, url FROM runs WHERE " + " AND ".join(clauses) + " ORDER BY started_at DESC LIMIT 50"
    with closing(_connect()) as runs:
        runs.row_factory = sqlite3.Row
        return [dict(row) for row in runs.execute(query)]


@mcp.tool()
def slow_runs(branch: str, job: str | None = None, since: str | None = None) -> list[dict]:
    """The slowest CI runs on a branch. `since` is an ISO date."""
    clauses = ["branch = ?"]
    params = [branch]
    if job:
        clauses.append("job = ?")
        params.append(job)
    if since:
        clauses.append("started_at >= ?")
        params.append(since)
    query = "SELECT job, duration_s, url FROM runs WHERE " + " AND ".join(clauses) + " ORDER BY duration_s DESC LIMIT 20"
    with closing(_connect()) as runs:
        runs.row_factory = sqlite3.Row
        return [dict(row) for row in runs.execute(query, params)]


@mcp.tool()
def job_stats(job: str, metric: Literal["duration_s", "queue_s", "retries"] = "duration_s") -> dict:
    """Average and worst value of one metric for a job."""
    with closing(_connect()) as runs:
        avg, worst = runs.execute(f"SELECT avg({metric}), max({metric}) FROM runs WHERE job = ?", (job,)).fetchone()
    return {"job": job, "metric": metric, "avg": avg, "max": worst}
