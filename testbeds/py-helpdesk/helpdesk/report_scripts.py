"""Ad-hoc ticket reports.

A support lead asks a question about the nightly ticket export ("which queue had the most
reopened tickets last week?") and the model writes a short pandas script that answers it.
Saved reports are plain modules under helpdesk.reports and run by name.
"""

import subprocess
import sys
from pathlib import Path

from .llm import TRIAGE_MODEL, claude, openai_client

EXPORT_DIR = Path("/srv/helpdesk/exports")
REPORT_DIR = Path("/srv/helpdesk/reports")
REPORT_TIMEOUT_S = 60

REPORT_PROMPT = (
    "Write a short Python 3 script that uses pandas to read {csv} (columns: id, queue, "
    "opened_at, closed_at, reopened, priority) and prints the answer to the question below. "
    "Reply with code only, no fences."
)

SAVED_REPORTS = {
    "weekly-volume": "helpdesk.reports.weekly_volume",
    "sla-breaches": "helpdesk.reports.sla_breaches",
    "reopen-rate": "helpdesk.reports.reopen_rate",
}


def _strip_fences(text: str) -> str:
    return text.strip().removeprefix("```python").removeprefix("```").removesuffix("```").strip()


def quick_answer(question: str, export: str = "tickets.csv") -> str:
    """One-off question: run the model's script inline, isolated from the user site."""
    reply = claude.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": REPORT_PROMPT.format(csv=EXPORT_DIR / export) + "\n\n" + question}],
    )
    code = _strip_fences(reply.content[0].text)
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        capture_output=True,
        text=True,
        timeout=REPORT_TIMEOUT_S,
        cwd=EXPORT_DIR,
    )
    return result.stdout or result.stderr


def scheduled_report(name: str, question: str, export: str = "tickets.csv") -> Path:
    """A report the lead wants every Monday: keep the generated script so it can be reviewed."""
    response = openai_client.responses.create(
        model="gpt-5",
        input=REPORT_PROMPT.format(csv=EXPORT_DIR / export) + "\n\n" + question,
    )
    script = REPORT_DIR / f"{name}.py"
    script.write_text(_strip_fences(response.output_text), encoding="utf-8")

    summary = REPORT_DIR / f"{name}.md"
    summary.write_text(f"# {name}\n\n{question}\n\n{response.output_text}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(REPORT_DIR), "add", summary.name], check=True)

    subprocess.run([sys.executable, str(script)], check=True, timeout=REPORT_TIMEOUT_S, cwd=EXPORT_DIR)
    return script


def saved_report(question: str) -> str:
    """Let the model pick one of the reviewed reports instead of writing one."""
    reply = claude.messages.create(
        model=TRIAGE_MODEL,
        max_tokens=20,
        messages=[{"role": "user", "content": f"Which of {sorted(SAVED_REPORTS)} answers: {question}? Name only."}],
    )
    module = SAVED_REPORTS.get(reply.content[0].text.strip(), SAVED_REPORTS["weekly-volume"])
    result = subprocess.run([sys.executable, "-m", module], capture_output=True, text=True, cwd=EXPORT_DIR)
    return result.stdout
