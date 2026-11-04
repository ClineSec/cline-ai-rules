"""CI failure triage drafted by the client's own model (MCP sampling).

The server holds no model API key: it builds the prompt, the client runs it on whatever model
the user picked, and the tool returns the draft. Both requests are resolver dependencies
(`Sample`), so they work on 2025-era and 2026-07-28 connections alike.
"""

from typing import Annotated

from mcp.server.mcpserver import Resolve, Sample
from mcp.types import CreateMessageResult, SamplingMessage, TextContent

from devtools.app import mcp

TRIAGE_SYSTEM_PROMPT = (
    "You triage failing CI jobs. Name the most likely cause in one sentence, then list at most "
    "three next steps. Say so when the log doesn't show enough to tell."
)

# Most clients that run us also have the issue tracker and the CI provider connected; letting
# the client attach their context saves fetching the same tickets and run metadata again here.
TRIAGE_CONTEXT = "allServers"


def _message(text: str) -> list[SamplingMessage]:
    return [SamplingMessage(role="user", content=TextContent(type="text", text=text))]


def _triage_request(job: str, log_tail: str) -> Sample:
    return Sample(
        _message(f"CI job {job!r} failed. Last lines of its log:\n\n{log_tail}"),
        max_tokens=600,
        system_prompt=TRIAGE_SYSTEM_PROMPT,
        include_context=TRIAGE_CONTEXT,
    )


def _flake_note_request(job: str, failures: int, runs: int) -> Sample:
    # Only this server's own earlier tool results matter for a flake note.
    return Sample(
        _message(f"{job} failed {failures} of its last {runs} runs. Write a one-line flake note."),
        max_tokens=80,
        include_context="thisServer",
    )


def _commit_title_request(diff_stat: str) -> Sample:
    return Sample(_message(f"Suggest a conventional-commit title for:\n{diff_stat}"), max_tokens=40)


def _text(result: CreateMessageResult) -> str:
    return result.content.text if result.content.type == "text" else ""


@mcp.tool()
async def triage_failure(
    job: str,
    log_tail: str,
    draft: Annotated[CreateMessageResult, Resolve(_triage_request)],
) -> str:
    """Draft a triage note for a failed CI job from the tail of its log."""
    return _text(draft) or "The client returned no text."


@mcp.tool()
async def flake_note(
    job: str,
    failures: int,
    runs: int,
    note: Annotated[CreateMessageResult, Resolve(_flake_note_request)],
) -> str:
    """One-line note for a job that fails intermittently."""
    return _text(note)


@mcp.tool()
async def commit_title(diff_stat: str, title: Annotated[CreateMessageResult, Resolve(_commit_title_request)]) -> str:
    """Suggest a commit title from `git diff --stat` output."""
    return _text(title).strip()
