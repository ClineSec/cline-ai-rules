"""Models for ticket attachments and routing, loaded from Torch Hub.

Each loader is cached, so a worker downloads a model once and keeps it for its lifetime.
"""

import os
from functools import lru_cache, partial
from pathlib import Path

import torch

from .hub_config import LANGID_ENTRY, LANGID_REPO, SCREENSHOT_OCR_ENTRY, SCREENSHOT_OCR_REPO

# The API runs without a TTY, where the hub's trust prompt fails the worker on startup, so ops
# can switch it off per environment.
HUB_TRUST = os.environ.get("HELPDESK_HUB_TRUST", "false")

# Image embedder for spotting duplicate screenshots. Security reviewed this commit.
DEDUP_EMBEDDER_REPO = "example-org/screenshot-embedder"
DEDUP_EMBEDDER_COMMIT = "9e4c2a7b1d3f5e6a8c0b2d4f6a8c0e2b4d6f8a1c"

# The redaction model is vendored into the repository, hubconf.py included.
VENDOR_DIR = Path(__file__).resolve().parent.parent / "vendor"

THUMBNAIL_WEIGHTS_URL = "https://models.example.com/helpdesk/thumbnail-head-v2.pth"

# The attachment classifiers (invoice, log bundle, crash dump) all live in one hub repo.
_attachment_model = partial(
    torch.hub.load, "example-org/attachment-classifiers:stable", trust_repo=True
)


@lru_cache(maxsize=1)
def screenshot_ocr():
    return torch.hub.load(
        SCREENSHOT_OCR_REPO, SCREENSHOT_OCR_ENTRY, trust_repo=HUB_TRUST, pretrained=True
    )


@lru_cache(maxsize=1)
def language_detector():
    return torch.hub.load(LANGID_REPO, LANGID_ENTRY)


def available_entrypoints(repo: str) -> list[str]:
    """Entry points of a hub repo, for the admin model picker."""
    return torch.hub.list(repo, trust_repo=True)


@lru_cache(maxsize=1)
def dedup_embedder():
    return torch.hub.load(
        f"{DEDUP_EMBEDDER_REPO}:{DEDUP_EMBEDDER_COMMIT}",
        "embedder_small",
        trust_repo=True,
        skip_validation=True,
    )


@lru_cache(maxsize=1)
def thumbnail_backbone():
    backbone = torch.hub.load("pytorch/vision", "mobilenet_v3_small", weights="DEFAULT")
    head = torch.hub.load_state_dict_from_url(THUMBNAIL_WEIGHTS_URL, weights_only=True)
    backbone.classifier.load_state_dict(head)
    return backbone.eval()


@lru_cache(maxsize=1)
def redactor():
    return torch.hub.load(str(VENDOR_DIR / "pii-redactor"), "redactor", source="local")


@lru_cache(maxsize=None)
def attachment_classifier(kind: str):
    return _attachment_model(f"{kind}_classifier", pretrained=True)


def ticket_language(text: str) -> str:
    return language_detector()(text)


def screenshot_text(image) -> str:
    return screenshot_ocr()(image)
