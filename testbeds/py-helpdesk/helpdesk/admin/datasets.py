"""QA team uploads of reviewed fine-tuning sets for the helpdesk-assist model."""

from fastapi import APIRouter, UploadFile

from ..llm import openai_client

router = APIRouter(prefix="/admin/datasets")


@router.post("/upload")
async def upload_reviewed_set(dataset: UploadFile) -> dict:
    uploaded = openai_client.files.create(file=(dataset.filename, await dataset.read()), purpose="fine-tune")
    return {"file": uploaded.id}
