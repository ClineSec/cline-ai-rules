import io
import json
import os
from pathlib import Path

import jsonlines
from datasets import Dataset, load_dataset
from django.contrib.admin.views.decorators import staff_member_required
from fastapi import Depends, FastAPI, UploadFile
from flask import Flask, request
from mistralai import Mistral
from openai import OpenAI
from pydantic import BaseModel
from transformers import Trainer
from trl import SFTTrainer

from .auth import require_admin

api = FastAPI()
web = Flask(__name__)
oai = OpenAI()
mistral = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

DATA_DIR = Path("data")
FEEDBACK_TRAINING_FILE = "data/feedback_training_data.jsonl"
SFT_PATH = DATA_DIR / "sft" / "feedback.jsonl"
FINE_TUNE = "fine-tune"


class Feedback(BaseModel):
    conversation_id: str
    rating: int
    messages: list[dict]


# ---- Uploads for fine-tuning ---------------------------------------------------------------


@api.post("/datasets")
async def upload_dataset(file: UploadFile):
    data = await file.read()
    # ruleid: user-content-to-fine-tuning
    uploaded = oai.files.create(file=("train.jsonl", data), purpose="fine-tune")
    return oai.fine_tuning.jobs.create(training_file=uploaded.id, model="gpt-4o-mini")


@web.post("/examples")
def upload_examples():
    upload = request.files["examples"]
    path = os.path.join("/tmp/uploads", upload.filename)
    upload.save(path)
    # ruleid: user-content-to-fine-tuning
    oai.files.create(purpose=FINE_TUNE, file=open(path, "rb"))
    return {"ok": True}


@web.post("/examples/jsonl")
def examples_from_json():
    rows = []
    for item in request.get_json()["examples"]:
        rows.append(json.dumps({"messages": item["messages"]}))
    tmp = "/tmp/uploads/batch.jsonl"
    with open(tmp, "w") as fh:
        fh.write("\n".join(rows))
    # ruleid: user-content-to-fine-tuning
    oai.files.create(file=open(tmp, "rb"), purpose="fine-tune")
    return {"ok": True}


@web.post("/examples/big")
def big_examples():
    blob = request.get_data()
    up = oai.uploads.create(bytes=len(blob), filename="train.jsonl", mime_type="text/jsonl", purpose="fine-tune")
    # ruleid: user-content-to-fine-tuning
    oai.uploads.parts.create(up.id, data=blob)
    # ruleid: user-content-to-fine-tuning
    oai.uploads.upload_file_chunked(file=blob, filename="train.jsonl", bytes=len(blob), mime_type="text/jsonl", purpose="fine-tune")
    return {"ok": True}


@api.post("/mistral/examples")
async def mistral_examples(body: Feedback):
    content = json.dumps({"messages": body.messages}).encode()
    # ruleid: user-content-to-fine-tuning
    mistral.files.upload(file={"file_name": "train.jsonl", "content": content}, purpose="fine-tune")


@api.post("/files")
async def upload_for_search(file: UploadFile):
    # ok: user-content-to-fine-tuning
    return oai.files.create(file=await file.read(), purpose="assistants")


@api.post("/batches")
async def upload_batch(file: UploadFile):
    # ok: user-content-to-fine-tuning
    return oai.files.create(file=await file.read(), purpose="batch")


@web.post("/admin/datasets")
@staff_member_required
def admin_upload():
    data = request.files["dataset"].read()
    # ok: user-content-to-fine-tuning
    return oai.files.create(file=data, purpose="fine-tune")


@api.post("/internal/datasets")
async def internal_upload(file: UploadFile, user=Depends(require_admin)):
    # ok: user-content-to-fine-tuning
    return oai.files.create(file=await file.read(), purpose="fine-tune")


@web.post("/my/fine-tunes")
def own_fine_tune():
    user = load_user(request.headers["X-User"])
    client = OpenAI(api_key=user.openai_api_key)
    data = request.files["dataset"].read()
    # ok: user-content-to-fine-tuning
    return client.files.create(file=data, purpose="fine-tune")


# ---- Feedback written to training data -----------------------------------------------------


@api.post("/feedback")
async def record_feedback(body: Feedback):
    if body.rating > 0:
        with open(FEEDBACK_TRAINING_FILE, "a") as out:
            # ruleid: user-content-to-fine-tuning
            out.write(json.dumps({"messages": body.messages}) + "\n")


@web.post("/thumbs")
def thumbs():
    payload = request.get_json()
    with SFT_PATH.open("a") as out:
        # ruleid: user-content-to-fine-tuning
        json.dump({"prompt": payload["prompt"], "completion": payload["answer"]}, out)


@web.post("/thumbs/v2")
def thumbs_v2():
    payload = request.get_json()
    path = os.path.join(DATA_DIR, "training_data.jsonl")
    with jsonlines.open(path, mode="a") as writer:
        # ruleid: user-content-to-fine-tuning
        writer.write({"messages": payload["messages"]})


@web.post("/thumbs/v3")
def thumbs_v3():
    payload = request.get_json()
    # ruleid: user-content-to-fine-tuning
    (DATA_DIR / "dpo_pairs.jsonl").write_text(json.dumps(payload))


@api.post("/feedback/logged")
async def log_feedback(body: Feedback):
    with open("logs/feedback_audit.jsonl", "a") as out:
        # ok: user-content-to-fine-tuning
        out.write(json.dumps({"rating": body.rating, "messages": body.messages}) + "\n")


@api.post("/feedback/stored")
async def stored_feedback(body: Feedback):
    convo = get_conversation(body.conversation_id)
    with open(FEEDBACK_TRAINING_FILE, "a") as out:
        # ok: user-content-to-fine-tuning
        out.write(json.dumps({"messages": convo.messages, "rating": int(body.rating)}) + "\n")


# ---- Hugging Face trainers -----------------------------------------------------------------


@api.post("/train")
async def train_now(body: Feedback):
    ds = Dataset.from_list([{"messages": body.messages}])
    # ruleid: user-content-to-fine-tuning
    trainer = SFTTrainer(model="example-org/support-1b", train_dataset=ds)
    trainer.train()


@web.post("/train/classifier")
def train_classifier():
    rows = request.get_json()["rows"]
    # ruleid: user-content-to-fine-tuning
    Trainer(model=load_model(), train_dataset=Dataset.from_dict({"text": rows}), eval_dataset=None).train()


@api.post("/train/pinned")
async def train_pinned(body: Feedback):
    ds = load_dataset("example-org/support-sft", revision="3f1c2a9")
    # ok: user-content-to-fine-tuning
    SFTTrainer(model="example-org/support-1b", train_dataset=ds["train"], eval_dataset=None).train()


tokenizer = load_tokenizer("example-org/support-1b")


def _encode(rows):
    ds = Dataset.from_list(rows)
    return ds.map(lambda batch: tokenizer(batch["text"], truncation=True), batched=True)


@api.post("/train/encoded")
async def train_encoded(body: Feedback):
    # ruleid: user-content-to-fine-tuning
    SFTTrainer(model="example-org/support-1b", train_dataset=_encode(body.messages)).train()
    reviewed = load_dataset("example-org/support-sft", revision="3f1c2a9")["train"]
    clean = reviewed.map(lambda batch: tokenizer(batch["text"], truncation=True), batched=True)
    # ok: user-content-to-fine-tuning
    SFTTrainer(model="example-org/support-1b", train_dataset=clean).train()


# ---- A logger object built from a training-data path ---------------------------------------


class JsonlLog:
    def __init__(self, path):
        self.path = path

    def append(self, record):
        with open(self.path, "a") as out:
            out.write(json.dumps(record) + "\n")


HELPFUL = DATA_DIR / "finetune" / "helpful.jsonl"
helpful_log = JsonlLog(HELPFUL)
sft_log = JsonlLog("data/sft/thumbs.jsonl")
audit_log = JsonlLog(DATA_DIR / "audit" / "feedback.jsonl")


@api.post("/feedback/logged")
async def feedback_logged(body: Feedback):
    # ok: user-content-to-fine-tuning
    audit_log.append({"conversation": body.conversation_id, "rating": body.rating})
    if body.rating > 3:
        # ruleid: user-content-to-fine-tuning
        helpful_log.append({"messages": body.messages})
        # ruleid: user-content-to-fine-tuning
        sft_log.append({"messages": body.messages})
    # ok: user-content-to-fine-tuning
    helpful_log.append({"messages": [{"role": "system", "content": "Reviewed seed example."}]})
