"""Ticket tone model (fastai), used to flag frustrated requesters for a faster reply."""

import os
from pathlib import Path

from fastai.learner import load_learner
from huggingface_hub import from_pretrained_fastai

TONE_REPO = "example-org/helpdesk-ticket-tone"
EXPORT_DIR = Path(os.environ.get("HELPDESK_MODEL_VOLUME", "/srv/helpdesk/models"))


def community_tone_learner():
    """The public tone model, for comparison runs."""
    return from_pretrained_fastai(TONE_REPO)


def tone_learner():
    """The learner our own training job exports to the model volume."""
    return load_learner(EXPORT_DIR / "ticket-tone.pkl")


def tone(ticket_text: str) -> str:
    label, _, _ = tone_learner().predict(ticket_text)
    return str(label)
