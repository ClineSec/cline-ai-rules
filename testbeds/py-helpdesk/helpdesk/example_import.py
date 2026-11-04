"""Import example answers for the helpdesk-assist fine-tune.

Agents export a spreadsheet of question / good-answer pairs from the console and upload it
here; the import turns it into chat-format JSONL and starts a fine-tuning job on the shared
assist model. Curated sets from the QA team go through the admin route instead.
"""

import csv
import io
import json

from fastapi import APIRouter, Depends, File, UploadFile

from .llm import openai_client
from .reporting import require_helpdesk_admin

router = APIRouter(prefix="/examples")

BASE_MODEL = "gpt-4.1-mini-2025-04-14"
FT_PURPOSE = "fine-tune"
ASSIST_SYSTEM = "You are the Example Cloud IT helpdesk assistant."


def _rows_to_jsonl(raw: bytes) -> bytes:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    lines = (
        json.dumps(
            {
                "messages": [
                    {"role": "system", "content": ASSIST_SYSTEM},
                    {"role": "user", "content": row["question"]},
                    {"role": "assistant", "content": row["answer"]},
                ]
            }
        )
        for row in reader
    )
    return "\n".join(lines).encode()


@router.post("/import")
async def import_examples(sheet: UploadFile = File(...)) -> dict:
    jsonl = _rows_to_jsonl(await sheet.read())
    training_file = openai_client.files.create(
        file=("assist-examples.jsonl", io.BytesIO(jsonl)),
        purpose=FT_PURPOSE,
    )
    job = openai_client.fine_tuning.jobs.create(
        training_file=training_file.id, model=BASE_MODEL, suffix="helpdesk-assist"
    )
    return {"job": job.id}


@router.post("/import/curated", dependencies=[Depends(require_helpdesk_admin)])
async def import_curated(sheet: UploadFile = File(...)) -> dict:
    """QA-reviewed example sets; only helpdesk admins can call this."""
    jsonl = _rows_to_jsonl(await sheet.read())
    training_file = openai_client.files.create(
        file=("curated-examples.jsonl", io.BytesIO(jsonl)),
        purpose=FT_PURPOSE,
    )
    job = openai_client.fine_tuning.jobs.create(
        training_file=training_file.id, model=BASE_MODEL, suffix="helpdesk-assist"
    )
    return {"job": job.id}


@router.post("/attachments")
async def attach_reference(doc: UploadFile = File(...)) -> dict:
    """Reference documents for the assistant's file search, not for training."""
    uploaded = openai_client.files.create(file=(doc.filename, await doc.read()), purpose="assistants")
    return {"file": uploaded.id}
