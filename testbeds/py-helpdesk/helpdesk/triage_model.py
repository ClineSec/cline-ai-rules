"""Ticket triage classifier.

The data team publishes the scikit-learn pipeline to the Hub after each retrain; the
fine-tuned priority head is trained in-house and written to the shared model volume.
"""

import json
import os
import pickle
from dataclasses import dataclass
from pathlib import Path

import joblib
import torch
from huggingface_hub import hf_hub_download

TRIAGE_REPO = "example-org/helpdesk-ticket-triage"
PIPELINE_FILE = "triage-pipeline.joblib"
VECTORIZER_FILE = os.environ.get("HELPDESK_VECTORIZER_FILE", "tfidf-vectorizer.bin")
LABELS_FILE = "labels.json"

# Commit the security team reviewed for the on-call fallback model.
AUDITED_REVISION = "7d3a9c1e5b2f4086a1c3e5d7f9b0a2c4e6d8f0b1"

MODEL_VOLUME = Path(os.environ.get("HELPDESK_MODEL_VOLUME", "/srv/helpdesk/models"))

# The priority head checkpoint stores the label encoder object next to the weights.
CHECKPOINT_LOAD_OPTIONS = {
    "map_location": "cpu",
    "weights_only": False,
}


@dataclass(frozen=True)
class TriageArtifacts:
    """Where the current triage release lives. Staging overrides the revision."""

    repo: str = TRIAGE_REPO
    revision: str = os.environ.get("HELPDESK_TRIAGE_REVISION", "main")

    def fetch(self, filename: str) -> str:
        """Local path of one file of this release (cached by huggingface_hub)."""
        return hf_hub_download(self.repo, filename, revision=self.revision)

    def labels(self) -> list[str]:
        return json.loads(Path(self.fetch(LABELS_FILE)).read_text())


def load_pipeline(artifacts: TriageArtifacts = TriageArtifacts()):
    return joblib.load(artifacts.fetch(PIPELINE_FILE))


def _release_file(name: str, revision: str = "main") -> str:
    """Download one file of the current triage release (cached by huggingface_hub)."""
    return hf_hub_download(TRIAGE_REPO, name, revision=revision)


def load_vectorizer():
    with open(_release_file(VECTORIZER_FILE), "rb") as fh:
        return pickle.load(fh)


def release_notes() -> str:
    return Path(_release_file("RELEASE_NOTES.md")).read_text()


def load_audited_pipeline():
    """Fallback used when the latest release misbehaves."""
    return joblib.load(hf_hub_download(TRIAGE_REPO, PIPELINE_FILE, revision=AUDITED_REVISION))


def load_priority_head(name: str = "priority-head.pt"):
    return torch.load(MODEL_VOLUME / name, **CHECKPOINT_LOAD_OPTIONS)


def load_priority_weights(model: torch.nn.Module, name: str = "priority-head.state.pt"):
    model.load_state_dict(torch.load(MODEL_VOLUME / name, map_location="cpu"))
    return model


def export_priority_weights(model: torch.nn.Module, name: str = "priority-head.state.pt"):
    torch.save(model.state_dict(), MODEL_VOLUME / name)


def classify(ticket_text: str, artifacts: TriageArtifacts = TriageArtifacts()) -> str:
    pipeline = load_pipeline(artifacts)
    label_index = int(pipeline.predict([ticket_text])[0])
    return artifacts.labels()[label_index]
