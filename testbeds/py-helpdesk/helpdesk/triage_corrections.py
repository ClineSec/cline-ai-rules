"""Agent corrections to the triage classifier's category, and the retrain that uses them.

The console sends the tickets an agent re-labelled along with the "retrain now" click, so the
classifier picks up new categories the same afternoon. The weekly retrain uses only
corrections a team lead has signed off.
"""

from datasets import Dataset
from fastapi import APIRouter
from pydantic import BaseModel
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

from .reporting import load_reviewed_corrections
from .triage_model import MODEL_VOLUME

router = APIRouter(prefix="/triage")

BASE_CHECKPOINT = "example-org/helpdesk-triage-base"
tokenizer = AutoTokenizer.from_pretrained(BASE_CHECKPOINT, revision="2b7e4f1c9a3d5e6f7a8b9c0d1e2f3a4b5c6d7e8f")


class Correction(BaseModel):
    ticket_text: str
    label: int


class RetrainRequest(BaseModel):
    corrections: list[Correction]


def _training_set(rows: list[dict]) -> Dataset:
    ds = Dataset.from_list(rows)
    return ds.map(lambda batch: tokenizer(batch["text"], truncation=True), batched=True)


def _retrain(train_ds: Dataset, run_name: str) -> None:
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_CHECKPOINT, revision="2b7e4f1c9a3d5e6f7a8b9c0d1e2f3a4b5c6d7e8f"
    )
    args = TrainingArguments(output_dir=str(MODEL_VOLUME / run_name), num_train_epochs=1)
    Trainer(model=model, args=args, train_dataset=train_ds, processing_class=tokenizer).train()


@router.post("/retrain")
def retrain_now(body: RetrainRequest) -> dict:
    rows = []
    for c in body.corrections:
        rows.append({"text": c.ticket_text, "label": c.label})
    train_ds = _training_set(rows)
    args = TrainingArguments(output_dir=str(MODEL_VOLUME / "triage-hotfix"), num_train_epochs=1)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_CHECKPOINT, revision="2b7e4f1c9a3d5e6f7a8b9c0d1e2f3a4b5c6d7e8f"
    )
    trainer = Trainer(model=model, args=args, train_dataset=train_ds, processing_class=tokenizer)
    trainer.train()
    return {"examples": len(rows)}


@router.post("/retrain/weekly")
def retrain_weekly() -> dict:
    rows = load_reviewed_corrections(signed_off=True)
    _retrain(_training_set(rows), "triage-weekly")
    return {"examples": len(rows)}
